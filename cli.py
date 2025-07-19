#!/usr/bin/env python3
"""
PRP CLI - Admin Process Management (Factor XII)
Centralized command-line interface for all admin tasks
"""

import click
import os
import sys
from pathlib import Path
from datetime import datetime
from logging_config import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)

@click.group()
@click.version_option(version='2.0.0', prog_name='PRP CLI')
def cli():
    """PRP AI Assistant Command Line Interface"""
    logger.info("cli_started", command=" ".join(sys.argv))

@cli.group()
def db():
    """Database management commands"""
    pass

@db.command()
@click.option('--url', envvar='DATABASE_URL', help='Database URL')
def migrate(url):
    """Run database migrations"""
    if not url:
        click.echo("❌ DATABASE_URL not found", err=True)
        sys.exit(1)
    
    logger.info("database_migration_started", database_url=url)
    
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command
        
        # Run Alembic migrations
        alembic_cfg = AlembicConfig('alembic.ini')
        command.upgrade(alembic_cfg, 'head')
        
        logger.info("database_migration_completed")
        click.echo("✅ Database migrations completed successfully")
    except Exception as e:
        logger.error("database_migration_failed", error=str(e))
        click.echo(f"❌ Migration failed: {e}", err=True)
        sys.exit(1)

@db.command()
@click.option('--url', envvar='DATABASE_URL', help='Database URL')
def create_tables(url):
    """Create database tables"""
    if not url:
        click.echo("❌ DATABASE_URL not found", err=True)
        sys.exit(1)
    
    try:
        from prp_models import create_tables
        create_tables(url)
        
        logger.info("database_tables_created", database_url=url)
        click.echo("✅ Database tables created successfully")
    except Exception as e:
        logger.error("database_table_creation_failed", error=str(e))
        click.echo(f"❌ Table creation failed: {e}", err=True)
        sys.exit(1)

@db.command()
@click.option('--days', default=90, help='Days to keep data')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted')
def cleanup(days, dry_run):
    """Clean up old data"""
    from prp_models import get_session, PRPAnalytics
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    logger.info("database_cleanup_started", days=days, dry_run=dry_run, cutoff_date=cutoff_date.isoformat())
    
    try:
        session = get_session()
        query = session.query(PRPAnalytics).filter(PRPAnalytics.created_at < cutoff_date)
        count = query.count()
        
        if dry_run:
            click.echo(f"🔍 Would delete {count} records older than {days} days")
        else:
            query.delete()
            session.commit()
            logger.info("database_cleanup_completed", records_deleted=count)
            click.echo(f"✅ Deleted {count} old records")
        
        session.close()
    except Exception as e:
        logger.error("database_cleanup_failed", error=str(e))
        click.echo(f"❌ Cleanup failed: {e}", err=True)
        sys.exit(1)

@cli.group()
def analytics():
    """Analytics and reporting commands"""
    pass

@analytics.command()
@click.option('--output', '-o', default='dashboard.json', help='Output file')
def export(output):
    """Export analytics dashboard data"""
    try:
        from PRPs.scripts.prp_analytics import StatelessPRPAnalytics
        from prp_models import create_tables, get_session
        import json
        
        # Initialize analytics
        engine = create_tables()
        session = get_session()
        analytics = StatelessPRPAnalytics(engine, None)  # Redis not needed for export
        
        # Get dashboard data
        data = analytics.get_dashboard_data()
        data['exported_at'] = datetime.utcnow().isoformat()
        
        # Write to file
        with open(output, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info("analytics_export_completed", output_file=output, records=len(data.get('recent_prps', [])))
        click.echo(f"✅ Analytics exported to {output}")
        
        session.close()
    except Exception as e:
        logger.error("analytics_export_failed", error=str(e))
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)

@analytics.command()
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json', 'csv']))
def report(output_format):
    """Generate analytics report"""
    try:
        from prp_models import get_session, PRPAnalytics
        from sqlalchemy import func
        
        session = get_session()
        
        # Query analytics data
        stats = session.query(
            func.count(PRPAnalytics.id).label('total_prps'),
            func.avg(PRPAnalytics.success_rate).label('avg_success'),
            func.avg(PRPAnalytics.performance_score).label('avg_performance')
        ).first()
        
        data = {
            'total_prps': stats.total_prps or 0,
            'average_success_rate': round(stats.avg_success or 0, 2),
            'average_performance_score': round(stats.avg_performance or 0, 2),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if output_format == 'json':
            click.echo(json.dumps(data, indent=2))
        elif output_format == 'csv':
            click.echo("metric,value")
            for key, value in data.items():
                click.echo(f"{key},{value}")
        else:  # table
            click.echo("📊 PRP Analytics Report")
            click.echo("=" * 30)
            click.echo(f"Total PRPs: {data['total_prps']}")
            click.echo(f"Avg Success Rate: {data['average_success_rate']}%")
            click.echo(f"Avg Performance: {data['average_performance_score']}")
            click.echo(f"Generated: {data['generated_at']}")
        
        logger.info("analytics_report_generated", format=output_format, **data)
        session.close()
    except Exception as e:
        logger.error("analytics_report_failed", error=str(e))
        click.echo(f"❌ Report generation failed: {e}", err=True)
        sys.exit(1)

@cli.group()
def health():
    """Health check and monitoring commands"""
    pass

@health.command()
def check():
    """Run comprehensive health check"""
    from scripts.health_check import main as health_main
    try:
        health_main()
    except SystemExit as e:
        sys.exit(e.code)

@health.command()
@click.option('--port', default=8000, help='Application port')
def monitor(port):
    """Monitor application health continuously"""
    import time
    import requests
    
    logger.info("health_monitoring_started", port=port)
    click.echo(f"🔍 Monitoring application health on port {port}")
    click.echo("Press Ctrl+C to stop...")
    
    try:
        while True:
            try:
                response = requests.get(f'http://localhost:{port}/health', timeout=5)
                status = "✅ HEALTHY" if response.status_code == 200 else f"⚠️  STATUS {response.status_code}"
                timestamp = datetime.now().strftime("%H:%M:%S")
                click.echo(f"[{timestamp}] {status}")
                
                logger.info("health_check_result", 
                           timestamp=timestamp,
                           status_code=response.status_code,
                           healthy=response.status_code == 200)
            except Exception as e:
                click.echo(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ UNHEALTHY - {e}")
                logger.error("health_check_failed", error=str(e))
            
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("health_monitoring_stopped")
        click.echo("\n🛑 Monitoring stopped")

@cli.command()
@click.option('--format', 'output_format', default='env', type=click.Choice(['env', 'json', 'yaml']))
def config(output_format):
    """Show current configuration"""
    try:
        from config import config as app_config
        
        config_vars = {
            'PRP_ENV': app_config.PRP_ENV,
            'PORT': app_config.PORT,
            'LOG_LEVEL': app_config.LOG_LEVEL,
            'ANALYTICS_RETENTION_DAYS': app_config.ANALYTICS_RETENTION_DAYS,
            'ENABLE_PREDICTIVE_ANALYSIS': app_config.ENABLE_PREDICTIVE_ANALYSIS,
            'ENABLE_SECURITY_SCANNING': app_config.ENABLE_SECURITY_SCANNING,
            'ENABLE_PERFORMANCE_MONITORING': app_config.ENABLE_PERFORMANCE_MONITORING
        }
        
        if output_format == 'json':
            import json
            click.echo(json.dumps(config_vars, indent=2))
        elif output_format == 'yaml':
            import yaml
            click.echo(yaml.dump(config_vars, default_flow_style=False))
        else:  # env format
            click.echo("# Current PRP Configuration")
            for key, value in config_vars.items():
                click.echo(f"{key}={value}")
        
        logger.info("configuration_displayed", format=output_format)
    except Exception as e:
        logger.error("configuration_display_failed", error=str(e))
        click.echo(f"❌ Failed to show configuration: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()