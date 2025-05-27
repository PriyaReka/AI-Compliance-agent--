from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging
from typing import Callable, Dict, Any

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        self.logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self.logger.info("Scheduler stopped")
    
    def add_job(self, 
                func: Callable, 
                job_id: str, 
                interval_minutes: int = 60,
                **kwargs) -> None:
        """Add a new job to the scheduler"""
        if job_id in self.jobs:
            self.remove_job(job_id)
        
        job = self.scheduler.add_job(
            func=func,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id=job_id,
            replace_existing=True,
            **kwargs
        )
        
        self.jobs[job_id] = job
        self.logger.info(f"Job {job_id} added with interval {interval_minutes} minutes")
    
    def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler"""
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            self.logger.info(f"Job {job_id} removed")
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a specific job"""
        if job_id not in self.jobs:
            return {"status": "not_found"}
        
        job = self.jobs[job_id]
        return {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "status": "running" if job.next_run_time else "stopped"
        }
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all jobs"""
        return {
            job_id: self.get_job_status(job_id)
            for job_id in self.jobs
        }
