using System.Data;
using System.Diagnostics;
using System.Text.Json;
using System.Threading.RateLimiting;
using Npgsql;
using System.Text;

var builder = WebApplication.CreateBuilder(args);
var connectionString = builder.Configuration.GetConnectionString("Postgres")
    ?? Environment.GetEnvironmentVariable("DATABASE_URL");
if (string.IsNullOrWhiteSpace(connectionString))
    throw new InvalidOperationException("DATABASE_URL or ConnectionStrings:Postgres must be configured.");
// Assignment contract has no login. Protected mode is an opt-in administrator-only safeguard.
var authMode = (Environment.GetEnvironmentVariable("AUTH_MODE") ?? "assignment").Trim().ToLowerInvariant();
if (authMode is not ("assignment" or "protected"))
    throw new InvalidOperationException("AUTH_MODE must be assignment or protected.");
var adminApiKey = Environment.GetEnvironmentVariable("ADMIN_API_KEY") ?? "";
if (authMode == "protected" && Encoding.UTF8.GetByteCount(adminApiKey) < 32)
    throw new InvalidOperationException("ADMIN_API_KEY must contain at least 32 UTF-8 bytes in protected mode.");
var holdDurationInput = Environment.GetEnvironmentVariable("HOLD_DURATION_SECONDS") ?? "600";
if (!int.TryParse(holdDurationInput, out var duration) || duration is < 1 or > 86400)
    throw new InvalidOperationException("HOLD_DURATION_SECONDS must be an integer between 1 and 86400.");
// Bound concurrent work per API process so overload does not exhaust database connections.
// Database constraints and row locking remain the source of correctness.
builder.Services.AddRateLimiter(options => {
    options.RejectionStatusCode = 429;
    options.OnRejected = async (rejection, _) => {
        var ctx = rejection.HttpContext;
        ctx.Response.Headers["Retry-After"] = "1";
        await ApiError.Create(ctx, 429, "RATE_LIMITED", "Too many requests; try again shortly").ExecuteAsync(ctx);
    };
    options.GlobalLimiter = PartitionedRateLimiter.Create<HttpContext, string>(context =>
        RateLimitPartition.GetConcurrencyLimiter("api", _ => new ConcurrencyLimiterOptions {
            PermitLimit = 128, QueueLimit = 128, QueueProcessingOrder = QueueProcessingOrder.OldestFirst
        }));
});
builder.Services.AddSingleton(new Db(connectionString, duration));
builder.Services.AddHostedService<ExpiryWorker>();
var app = builder.Build();
app.Use(async (context, next) => {
    var correlation = context.Request.Headers["X-Request-Id"].ToString();
    if (string.IsNullOrWhiteSpace(correlation) || correlation.Length > 100) correlation = Guid.NewGuid().ToString("N");
    context.TraceIdentifier = correlation;
    context.Response.Headers["X-Request-Id"] = correlation;
    var timer = Stopwatch.StartNew();
    try {
        using (app.Logger.BeginScope(new Dictionary<string,object> { ["RequestId"] = correlation })) await next();
    } finally {
        timer.Stop();
        HttpTelemetry.Record(context.Request.Method, context.Response.StatusCode, timer.Elapsed.TotalMilliseconds);
        app.Logger.LogInformation("HTTP {Method} {Path} -> {StatusCode} in {ElapsedMs}ms",
            context.Request.Method, context.Request.Path, context.Response.StatusCode, timer.Elapsed.TotalMilliseconds);
    }
});
app.UseRateLimiter();
app.Use(async (context, next) => {
    try { await next(); }
    catch (PostgresException ex) when (ex.SqlState is "23505" or "23514" or "23503") {
        if (!context.Response.HasStarted) {
            context.Response.StatusCode = ex.SqlState == "23505" ? 409 : 400;
            await ApiError.Create(context, context.Response.StatusCode, ex.SqlState, "Database constraint violation").ExecuteAsync(context);
        }
    }
    catch (PostgresException ex) when (ex.SqlState is "55P03" or "40P01" or "40001") {
        app.Logger.LogWarning(ex, "Database contention / retryable failure");
        if (!context.Response.HasStarted) {
            context.Response.StatusCode = 503;
            context.Response.Headers["Retry-After"] = "1";
            await ApiError.Create(context, 503, "DB_CONTENTION", "System busy, please retry shortly").ExecuteAsync(context);
        }
    }
    catch (BadHttpRequestException ex) {
        if (!context.Response.HasStarted) {
            context.Response.StatusCode = 400;
            await ApiError.Create(context, 400, "INVALID_BODY", "Invalid request body").ExecuteAsync(context);
        }
    }
    catch (JsonException) {
        if (!context.Response.HasStarted) {
            context.Response.StatusCode = 400;
            await ApiError.Create(context, 400, "INVALID_JSON", "Invalid JSON").ExecuteAsync(context);
        }
    }
    catch (NpgsqlException ex) {
        app.Logger.LogError(ex, "Database unavailable");
        if (!context.Response.HasStarted) {
            context.Response.StatusCode = 503;
            await ApiError.Create(context, 503, "DATABASE_UNAVAILABLE", "Database temporarily unavailable").ExecuteAsync(context);
        }
    }
    catch (Exception ex) {
        app.Logger.LogError(ex, "Unhandled request error");
        if (!context.Response.HasStarted) {
            context.Response.StatusCode = 500;
            await ApiError.Create(context, 500, "INTERNAL_ERROR", "Unexpected server error").ExecuteAsync(context);
        }
    }
});

// The database is the source of truth. Startup retries accommodate first-time Postgres setup.
using (var scope = app.Services.CreateScope()) {
    var db = scope.ServiceProvider.GetRequiredService<Db>();
    await db.InitializeAsync();
}
app.MapGet("/healthz", () => Results.Ok(new { status = "ok" }));
app.MapGet("/readyz", async (Db db) => {
    try {
        await using var connection = await db.OpenAsync();
        await using var command = new NpgsqlCommand("SELECT 1", connection);
        await command.ExecuteScalarAsync();
        return Results.Ok(new { status = "ready" });
    } catch { return Results.StatusCode(503); }
});

app.MapGet("/admin/auth-check", (HttpContext ctx) =>
    AdminKeyAuthorization.IsAuthorized(ctx, authMode, adminApiKey)
        ? Results.Ok(new { authorized = true, mode = authMode })
        : ApiError.Create(ctx, 401, "ADMIN_UNAUTHORIZED", "Administrator credentials required"));
app.MapPost("/classes", async (ClassCreate? input, Db db, HttpContext ctx) => {
    if (!AdminKeyAuthorization.IsAuthorized(ctx, authMode, adminApiKey))
        return ApiError.Create(ctx, 401, "ADMIN_UNAUTHORIZED", "Administrator credentials required");
    var name = input?.Name?.Trim();
    if (input is null || string.IsNullOrWhiteSpace(name) || name.Length > 150 || input.TotalSeats <= 0 || input.TotalSeats > 1_000_000)
        return ApiError.Create(ctx, 400, "INVALID_INPUT", "Valid name and totalSeats (1..1000000) required");
    await using var con = await db.OpenAsync();
    await using var cmd = new NpgsqlCommand("INSERT INTO classes(name,total_seats) VALUES (@n,@s) RETURNING id", con);
    cmd.Parameters.AddWithValue("n", name);cmd.Parameters.AddWithValue("s", input.TotalSeats);
    var id = (Guid)(await cmd.ExecuteScalarAsync())!;
    return Results.Created($"/classes/{Db.Id("c",id)}", new { id = Db.Id("c",id), name, totalSeats = input.TotalSeats });
});
app.MapGet("/classes", async (Db db) => {
    await using var con = await db.OpenAsync();
    const string sql = """
    SELECT c.id,c.name,c.total_seats,
      COUNT(h.id) FILTER (WHERE h.status='HELD' AND h.expires_at > clock_timestamp())::int AS held,
      COUNT(h.id) FILTER (WHERE h.status='CONFIRMED')::int AS confirmed
    FROM classes c LEFT JOIN holds h ON h.class_id=c.id GROUP BY c.id ORDER BY c.created_at,c.name
    """;
    await using var cmd = new NpgsqlCommand(sql, con);
    await using var r = await cmd.ExecuteReaderAsync();
    var list = new List<object>();
    while (await r.ReadAsync()) list.Add(Db.ClassSummary(r));
    return Results.Ok(list);
});
app.MapGet("/classes/{classId}", async (string classId, Db db, HttpContext ctx) => {
    if (!Db.ParseId(classId,"c",out var id)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "Invalid classId");
    await using var con = await db.OpenAsync();
    const string sql = """
    SELECT c.id,c.name,c.total_seats,
      (SELECT COUNT(*)::int FROM holds h WHERE h.class_id=c.id AND h.status='HELD' AND h.expires_at > clock_timestamp()) held,
      (SELECT COUNT(*)::int FROM holds h WHERE h.class_id=c.id AND h.status='CONFIRMED') confirmed FROM classes c WHERE c.id=@id
    """;
    await using var cmd = new NpgsqlCommand(sql,con);cmd.Parameters.AddWithValue("id",id);
    await using var r = await cmd.ExecuteReaderAsync();
    return await r.ReadAsync() ? Results.Ok(Db.ClassSummary(r)) : ApiError.Create(ctx, 404, "NOT_FOUND", "Class not found");
});
app.MapPost("/classes/{classId}/holds", async (string classId, HttpContext ctx, Db db) => {
    if (!Db.ParseId(classId,"c",out var classGuid)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "Invalid classId");
    if (!Db.Student(ctx,out var student)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "X-Student-Id must contain exactly 17 digits");
    await using var con=await db.OpenAsync();await using var tx=await con.BeginTransactionAsync(IsolationLevel.ReadCommitted);
    var total=await db.LockClassAsync(con,tx,classGuid);
    if (total is null) return ApiError.Create(ctx, 404, "NOT_FOUND", "Class not found");
    await db.ExpireClassAsync(con,tx,classGuid);
    await using (var cmd=new NpgsqlCommand("SELECT EXISTS (SELECT 1 FROM holds WHERE class_id=@c AND student_id=@s AND status IN ('HELD','CONFIRMED'))",con,tx)) {
        cmd.Parameters.AddWithValue("c",classGuid);cmd.Parameters.AddWithValue("s",student);
        if ((bool)(await cmd.ExecuteScalarAsync())!) return ApiError.Create(ctx, 409, "CONFLICT", "Student already has an active admission for this class");
    }
    await using (var cmd=new NpgsqlCommand("SELECT COUNT(*)::int FROM holds WHERE class_id=@c AND status IN ('HELD','CONFIRMED')",con,tx)) {
        cmd.Parameters.AddWithValue("c",classGuid);
        if ((int)(await cmd.ExecuteScalarAsync())! >= total.Value) return ApiError.Create(ctx, 409, "CONFLICT", "No available seats");
    }
    var holdId=Guid.NewGuid(); DateTime expiry;
    await using (var cmd=new NpgsqlCommand("INSERT INTO holds(id,class_id,student_id,status,expires_at) VALUES (@id,@c,@s,'HELD',clock_timestamp()+(@seconds * interval '1 second')) RETURNING expires_at",con,tx)) {
        cmd.Parameters.AddWithValue("id",holdId);cmd.Parameters.AddWithValue("c",classGuid);cmd.Parameters.AddWithValue("s",student);cmd.Parameters.AddWithValue("seconds",db.Duration);
        expiry=(DateTime)(await cmd.ExecuteScalarAsync())!;
    }
    await tx.CommitAsync();
    return Results.Created($"/holds/{Db.Id("h",holdId)}",new { holdId=Db.Id("h",holdId),classId,studentId=student,status="HELD",expiresAt=expiry });
});
app.MapGet("/holds/{holdId}",async (string holdId,Db db,HttpContext ctx) => {
    if(!Db.ParseId(holdId,"h",out var id)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "Invalid holdId");
    await using var con=await db.OpenAsync();
    await using var cmd=new NpgsqlCommand("SELECT class_id,CASE WHEN status='HELD' AND expires_at<=clock_timestamp() THEN 'EXPIRED' ELSE status END,expires_at FROM holds WHERE id=@id",con);cmd.Parameters.AddWithValue("id",id);
    await using var r=await cmd.ExecuteReaderAsync();
    if(!await r.ReadAsync()) return ApiError.Create(ctx, 404, "NOT_FOUND", "Hold not found");
    var classId=Db.Id("c",r.GetGuid(0));var status=r.GetString(1);var expiry=r.GetDateTime(2);
    return Results.Ok(new {holdId,classId,status,expiresAt=expiry});
});
// One code path for both state transitions: consistent locking, ownership and expiry checks.
app.MapPost("/holds/{holdId}/confirm", (string holdId, HttpContext ctx, Db db) => HoldTransitionService.ExecuteAsync(holdId, ctx, db, true));
app.MapDelete("/holds/{holdId}", (string holdId, HttpContext ctx, Db db) => HoldTransitionService.ExecuteAsync(holdId, ctx, db, false));
app.MapGet("/me/holds",async (HttpContext ctx,Db db) => {
    if(!Db.Student(ctx,out var student)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "Invalid X-Student-Id");
    await using var con=await db.OpenAsync();
    await using var cmd=new NpgsqlCommand("SELECT h.id,h.class_id,c.name,CASE WHEN h.status='HELD' AND h.expires_at<=clock_timestamp() THEN 'EXPIRED' ELSE h.status END,h.expires_at FROM holds h JOIN classes c ON c.id=h.class_id WHERE h.student_id=@s ORDER BY h.created_at DESC",con);
    cmd.Parameters.AddWithValue("s",student);await using var r=await cmd.ExecuteReaderAsync();var rows=new List<object>();
    while(await r.ReadAsync()) {
        var status=r.GetString(3);var expiry=r.GetDateTime(4);
        rows.Add(new {holdId=Db.Id("h",r.GetGuid(0)),classId=Db.Id("c",r.GetGuid(1)),className=r.GetString(2),status,expiresAt=expiry});
    }
    return Results.Ok(rows);
});

app.Run();
