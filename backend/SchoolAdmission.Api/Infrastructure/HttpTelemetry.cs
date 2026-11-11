using System.Diagnostics;
using System.Diagnostics.Metrics;

/// <summary>Low-overhead counters; attach a Meter listener/OTel exporter in production.</summary>
internal static class HttpTelemetry {
    private static readonly Meter Meter = new("SchoolAdmission.Http", "1.0.0");
    private static readonly Counter<long> Requests = Meter.CreateCounter<long>("http.server.requests");
    private static readonly Histogram<double> Duration = Meter.CreateHistogram<double>("http.server.duration.ms", "ms");
    internal static void Record(string method, int status, double durationMs) {
        var tags = new TagList { { "http.request.method", method }, { "http.response.status_code", status } };
        Requests.Add(1, tags);
        Duration.Record(durationMs, tags);
    }
}
