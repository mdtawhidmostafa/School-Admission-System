using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

sealed class ExpiryWorker(Db db,ILogger<ExpiryWorker> log):BackgroundService {
    protected override async Task ExecuteAsync(CancellationToken stoppingToken) {
        using var timer=new PeriodicTimer(TimeSpan.FromSeconds(3));
        while(!stoppingToken.IsCancellationRequested) {
            try {await db.CleanupAsync(stoppingToken);}catch(OperationCanceledException) when(stoppingToken.IsCancellationRequested){break;}
            catch(Exception ex){log.LogWarning(ex,"Expiry cleanup postponed");}
            try {if(!await timer.WaitForNextTickAsync(stoppingToken))break;}catch(OperationCanceledException){break;}
        }
    }
}
