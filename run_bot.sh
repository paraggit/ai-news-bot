#!/bin/bash
cd "/home/pi5/Documents/ai-news-bot"
export PYTHONPATH="/home/pi5/Documents/ai-news-bot"
export PYTHONUNBUFFERED=1
exec "/home/pi5/.cache/pypoetry/virtualenvs/ai-news-aggregator-AuUtrNQD-py3.11/bin/python" -m ai_news_bot.main
