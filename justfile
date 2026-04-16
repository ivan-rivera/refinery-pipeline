# refinery-pipeline — development commands

install:
    uv sync --all-groups

run *ARGS:
    uv run pipeline run {{ARGS}}

lint:
    uv run pre-commit run --all-files

test:
    uv run pytest tests/ -v --cov=src --cov-report=term-missing

coverage:
    uv run pytest tests/ -v --cov=src --cov-report=html

version-check:
    uv run cz bump --dry-run --yes || [ $? -eq 21 ]

schedule:
    mkdir -p $HOME/Library/Logs/refinery-pipeline
    cp scheduler/com.ivan-rivera.refinery-pipeline.plist $HOME/Library/LaunchAgents/com.ivan-rivera.refinery-pipeline.plist
    launchctl bootstrap gui/$(id -u) $HOME/Library/LaunchAgents/com.ivan-rivera.refinery-pipeline.plist
    @echo "Scheduled: com.ivan-rivera.refinery-pipeline"

unschedule:
    launchctl bootout gui/$(id -u) $HOME/Library/LaunchAgents/com.ivan-rivera.refinery-pipeline.plist
    rm -f $HOME/Library/LaunchAgents/com.ivan-rivera.refinery-pipeline.plist
    @echo "Unscheduled: com.ivan-rivera.refinery-pipeline"

schedule-status:
    launchctl list | grep refinery-pipeline || echo "Not scheduled"

logs:
    tail -f $HOME/Library/Logs/refinery-pipeline/stdout.log
