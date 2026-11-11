/// <summary>Compatibility-first error response: existing `error` field remains stable.</summary>
internal static class ApiError {
    internal static IResult Create(HttpContext context, int status, string code, string message) =>
        Results.Json(new { error = message, code, requestId = context.TraceIdentifier }, statusCode: status);
}
