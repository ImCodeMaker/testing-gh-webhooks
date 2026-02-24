import sys
import traceback
sys.path.append('.')
from app.services.ai.prompt import REVIEW_PROMPT_TEMPLATE
try:
    REVIEW_PROMPT_TEMPLATE.format(repo="repo", title="title", filename="filename", diff="diff")
    print("Success")
except Exception as e:
    print(f"Error: {repr(e)}")
