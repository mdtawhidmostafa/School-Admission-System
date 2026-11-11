using Npgsql;

/// <summary>Serializes hold transitions on the parent class row and checks ownership.</summary>
internal static class HoldTransitionService
{
    // All mutations lock the parent class before touching holds, including the expiry worker.
    internal static async Task<IResult> ExecuteAsync(string holdId, HttpContext ctx, Db db, bool confirm) {
        if (!Db.ParseId(holdId, "h", out var id)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "Invalid holdId");
        if (!Db.Student(ctx, out var student)) return ApiError.Create(ctx, 400, "INVALID_INPUT", "Invalid X-Student-Id");

        await using var con = await db.OpenAsync();
        await using var tx = await con.BeginTransactionAsync();
        var classId = await db.FindClassForHoldAsync(con, tx, id);
        if (classId is null) return ApiError.Create(ctx, 404, "NOT_FOUND", "Hold not found");
        await db.LockClassAsync(con, tx, classId.Value);
        await db.ExpireClassAsync(con, tx, classId.Value);

        string owner, currentStatus;
        await using (var cmd = new NpgsqlCommand("SELECT student_id,status FROM holds WHERE id=@id FOR UPDATE", con, tx)) {
            cmd.Parameters.AddWithValue("id", id);
            await using var reader = await cmd.ExecuteReaderAsync();
            if (!await reader.ReadAsync()) return ApiError.Create(ctx, 404, "NOT_FOUND", "Hold not found");
            owner = reader.GetString(0);
            currentStatus = reader.GetString(1);
        }
        if (owner != student) return ApiError.Create(ctx, 403, "FORBIDDEN", "This is not your admission");

        // A repeated successful request has the same effect as the first request.
        if (confirm && currentStatus == "CONFIRMED") {
            await tx.CommitAsync();
            return Results.Ok(new { holdId, status = "CONFIRMED" });
        }
        if (!confirm && currentStatus == "CANCELLED") {
            await tx.CommitAsync();
            return Results.NoContent();
        }
        if (currentStatus != "HELD")
            return ApiError.Create(ctx, 409, "INVALID_HOLD_STATE", "Only active HELD admissions can be changed (current status: " + currentStatus + ")");

        var nextStatus = confirm ? "CONFIRMED" : "CANCELLED";
        var sql = confirm
            ? "UPDATE holds SET status='CONFIRMED', confirmed_at=clock_timestamp() WHERE id=@id AND status='HELD'"
            : "UPDATE holds SET status='CANCELLED' WHERE id=@id AND status='HELD'";
        await using (var update = new NpgsqlCommand(sql, con, tx)) {
            update.Parameters.AddWithValue("id", id);
            if (await update.ExecuteNonQueryAsync() != 1) throw new InvalidOperationException("Hold transition failed");
        }
        await tx.CommitAsync();
        return confirm ? Results.Ok(new { holdId, status = nextStatus }) : Results.NoContent();
    }

}
