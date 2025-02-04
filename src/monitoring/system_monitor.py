from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import psutil
import asyncio

class SystemMonitor:
    """Monitors system health and performance"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.running = False
        
        # Define thresholds
        self.thresholds = {
            "cpu_percent": 80.0,  # CPU usage threshold
            "memory_percent": 85.0,  # Memory usage threshold
            "disk_percent": 90.0,  # Disk usage threshold
            "api_latency": 2000,  # API response time in ms
            "error_rate": 0.05  # Error rate threshold (5%)
        }

    async def start(self):
        """Start system monitoring"""
        self.running = True
        self.logger.info("System monitoring started")
        
        while self.running:
            try:
                # Collect metrics
                await self._collect_metrics()
                
                # Check thresholds and generate alerts
                await self._check_thresholds()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in system monitor: {str(e)}")
                await asyncio.sleep(60)

    async def stop(self):
        """Stop system monitoring"""
        self.running = False
        self.logger.info("System monitoring stopped")

    async def _collect_metrics(self):
        """Collect system metrics"""
        try:
            self.metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory": dict(psutil.virtual_memory()._asdict()),
                    "disk": dict(psutil.disk_usage('/')._asdict()),
                    "network": dict(psutil.net_io_counters()._asdict())
                },
                "application": {
                    "active_characters": await self._count_active_characters(),
                    "api_metrics": await self._get_api_metrics(),
                    "error_counts": await self._get_error_counts()
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")

    async def _check_thresholds(self):
        """Check metrics against thresholds"""
        if not self.metrics:
            return
            
        system = self.metrics["system"]
        app = self.metrics["application"]
        
        # Check CPU usage
        if system["cpu_percent"] > self.thresholds["cpu_percent"]:
            await self._create_alert(
                "high_cpu_usage",
                f"CPU usage at {system['cpu_percent']}%"
            )
            
        # Check memory usage
        if system["memory"]["percent"] > self.thresholds["memory_percent"]:
            await self._create_alert(
                "high_memory_usage",
                f"Memory usage at {system['memory']['percent']}%"
            )
            
        # Check disk usage
        if system["disk"]["percent"] > self.thresholds["disk_percent"]:
            await self._create_alert(
                "high_disk_usage",
                f"Disk usage at {system['disk']['percent']}%"
            )
            
        # Check API metrics
        api_metrics = app["api_metrics"]
        if api_metrics["average_latency"] > self.thresholds["api_latency"]:
            await self._create_alert(
                "high_api_latency",
                f"API latency at {api_metrics['average_latency']}ms"
            )
            
        # Check error rate
        error_rate = app["error_counts"]["rate"]
        if error_rate > self.thresholds["error_rate"]:
            await self._create_alert(
                "high_error_rate",
                f"Error rate at {error_rate*100}%"
            )

    async def _create_alert(self, alert_type: str, message: str):
        """Create system alert"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self.metrics
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"System Alert: {message}")
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    async def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "status": "healthy" if not self.alerts else "warning",
            "metrics": self.metrics,
            "recent_alerts": self.alerts[-5:],  # Last 5 alerts
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _count_active_characters(self) -> int:
        """Count active characters"""
        # This would be implemented to check database
        return 0

    async def _get_api_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics"""
        # This would be implemented to get actual API metrics
        return {
            "requests_per_minute": 0,
            "average_latency": 0,
            "success_rate": 1.0
        }

    async def _get_error_counts(self) -> Dict[str, Any]:
        """Get error statistics"""
        # This would be implemented to get actual error counts
        return {
            "total": 0,
            "rate": 0.0,
            "by_type": {}
        } 