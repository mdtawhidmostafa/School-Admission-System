using System.Security.Cryptography;
using System.Text;

internal static class AdminKeyAuthorization
{
    // Authorization is enforced on the server for class creation; UI visibility is not security.
    // A fixed-time comparison avoids leaking matching-prefix information.
    internal static bool IsAuthorized(HttpContext context, string mode, string expectedKey) {
        if (mode == "assignment") return true;
        var candidate = context.Request.Headers["X-Admin-Key"].ToString();
        var candidateBytes = SHA256.HashData(Encoding.UTF8.GetBytes(candidate));
        var expectedBytes = SHA256.HashData(Encoding.UTF8.GetBytes(expectedKey));
        return !string.IsNullOrEmpty(candidate) && CryptographicOperations.FixedTimeEquals(candidateBytes, expectedBytes);
    }
}
