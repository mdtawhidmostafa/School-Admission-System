using System.Text.RegularExpressions;
using System.Security.Cryptography;
using Npgsql;

sealed class Db(string cs,int duration) {
    public int Duration => duration;
    public static string Id(string prefix, Guid id) => prefix+"_"+id.ToString("N");
    public static bool ParseId(string raw,string prefix,out Guid guid) => Guid.TryParseExact(raw.StartsWith(prefix+"_")?raw[(prefix.Length+1)..]:"","N",out guid);
    public static bool Student(HttpContext ctx,out string value) {
        value=ctx.Request.Headers["X-Student-Id"].ToString();return Regex.IsMatch(value,@"^[0-9]{17}$",RegexOptions.CultureInvariant);
    }
    public static object ClassSummary(NpgsqlDataReader r) {
        var total=r.GetInt32(2);var held=r.GetInt32(3);var confirmed=r.GetInt32(4);
        return new {id=Id("c",r.GetGuid(0)),name=r.GetString(1),totalSeats=total,heldSeats=held,confirmedSeats=confirmed,availableSeats=Math.Max(0,total-held-confirmed)};
    }
    public async Task<NpgsqlConnection> OpenAsync() {var con=new NpgsqlConnection(cs);await con.OpenAsync();return con;}
    public async Task InitializeAsync() {
        for(var attempt=0;attempt<35;attempt++) {
            try {
                await using var con=await OpenAsync();
                // One migration runner at a time: all three replicas start simultaneously.
                // Session-level advisory lock is automatically released if connection closes.
                await using (var gate = new NpgsqlCommand("SELECT pg_advisory_lock(71421026)", con))
                    await gate.ExecuteNonQueryAsync();
                try {
                await using (var begin = new NpgsqlCommand("BEGIN",con)) await begin.ExecuteNonQueryAsync();
                try {
                    await using (var ledger = new NpgsqlCommand("CREATE TABLE IF NOT EXISTS schema_migrations (version varchar(80) PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT clock_timestamp(), checksum_sha256 varchar(64))", con)) await ledger.ExecuteNonQueryAsync();
                    // Upgrade legacy v11 ledgers without replaying old migrations. All future runs compare checksums.
                    await using (var column = new NpgsqlCommand("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum_sha256 varchar(64)",con)) await column.ExecuteNonQueryAsync();
                    var folder = Path.Combine(AppContext.BaseDirectory, "Migrations");
                    foreach (var file in Directory.GetFiles(folder,"*.sql").OrderBy(Path.GetFileName,StringComparer.Ordinal)) {
                        var version = Path.GetFileName(file);
                        var sql = await File.ReadAllTextAsync(file);
                        var checksum = Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(sql))).ToLowerInvariant();
                        await using var seen = new NpgsqlCommand("SELECT checksum_sha256 FROM schema_migrations WHERE version=@version", con);
                        seen.Parameters.AddWithValue("version", version);
                        var existing = await seen.ExecuteScalarAsync();
                        if (existing is not null) {
                            // v11 did not record checksums: pin the reviewed initial migration on first v12 start.
                            if (existing is DBNull) {
                                await using var pin = new NpgsqlCommand("UPDATE schema_migrations SET checksum_sha256=@sha WHERE version=@version AND checksum_sha256 IS NULL", con);
                                pin.Parameters.AddWithValue("sha", checksum);
                                pin.Parameters.AddWithValue("version", version);
                                await pin.ExecuteNonQueryAsync();
                            } else if (!string.Equals((string)existing, checksum, StringComparison.Ordinal)) {
                                throw new InvalidOperationException($"Migration checksum mismatch: {version}. Restore the reviewed migration file; do not edit applied SQL.");
                            }
                            continue;
                        }
                        await using (var migration = new NpgsqlCommand(sql,con)) await migration.ExecuteNonQueryAsync();
                        await using var record = new NpgsqlCommand("INSERT INTO schema_migrations(version,checksum_sha256) VALUES(@version,@sha)",con);
                        record.Parameters.AddWithValue("version",version);
                        record.Parameters.AddWithValue("sha",checksum);
                        await record.ExecuteNonQueryAsync();
                    }
                    await using var commit = new NpgsqlCommand("COMMIT",con);
                    await commit.ExecuteNonQueryAsync();
                } catch {
                    await using var rollback = new NpgsqlCommand("ROLLBACK",con);
                    await rollback.ExecuteNonQueryAsync();
                    throw;
                }
                } finally {
                    await using var release = new NpgsqlCommand("SELECT pg_advisory_unlock(71421026)", con);
                    await release.ExecuteNonQueryAsync();
                }
                return;
            } catch (NpgsqlException) when (attempt<34) {await Task.Delay(1000);}
        }
    }
    public async Task<int?> LockClassAsync(NpgsqlConnection con,NpgsqlTransaction tx,Guid id) {
        await using var cmd=new NpgsqlCommand("SELECT total_seats FROM classes WHERE id=@c FOR UPDATE",con,tx);
        cmd.Parameters.AddWithValue("c",id);var result=await cmd.ExecuteScalarAsync();return result is null?null:(int)result;
    }
    public async Task ExpireClassAsync(NpgsqlConnection con,NpgsqlTransaction tx,Guid id) {
        await using var cmd=new NpgsqlCommand("UPDATE holds SET status='EXPIRED' WHERE class_id=@c AND status='HELD' AND expires_at<=clock_timestamp()",con,tx);
        cmd.Parameters.AddWithValue("c",id);await cmd.ExecuteNonQueryAsync();
    }
    public async Task<Guid?> FindClassForHoldAsync(NpgsqlConnection con,NpgsqlTransaction tx,Guid id) {
        await using var cmd=new NpgsqlCommand("SELECT class_id FROM holds WHERE id=@id",con,tx);cmd.Parameters.AddWithValue("id",id);
        return await cmd.ExecuteScalarAsync() is Guid g?g:null;
    }
    public async Task CleanupAsync(CancellationToken token) {
        await using var con=await OpenAsync();
        // Class locks ensure cleanup uses the same serialization protocol as all mutations.
        await using var cmd=new NpgsqlCommand("SELECT DISTINCT class_id FROM holds WHERE status='HELD' AND expires_at<=clock_timestamp() LIMIT 200",con);
        var ids=new List<Guid>();await using(var r=await cmd.ExecuteReaderAsync(token)) while(await r.ReadAsync(token)) ids.Add(r.GetGuid(0));
        foreach(var id in ids) {
            await using var tx=await con.BeginTransactionAsync(token);
            await LockClassAsync(con,tx,id);await ExpireClassAsync(con,tx,id);
            await tx.CommitAsync(token);
        }
    }
}
