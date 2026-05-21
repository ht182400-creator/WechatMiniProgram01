# -*- coding: utf-8 -*-
"""快速启动脚本（无反代）"""
import uvicorn
uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=False)
