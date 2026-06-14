#!/bin/bash
cd ~/projects/goofish-cli-ext
source .venv/bin/activate
python -m goofish_cli_ext.commands.cron_price_watch
