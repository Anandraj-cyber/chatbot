import duckdb
import uvicorn
import asyncio
import json
import os
import re
from groq import Groq
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware  