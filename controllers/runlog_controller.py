from fastapi import HTTPException, status
from src.module3_NPL_search.parser import RunLogParser

# Create ONE parser instance (loads model once)
_parser = RunLogParser()  # if you want a model path later, set it here

def parse_runlog(text: str) -> dict:
    try:
        return _parser.parse(text)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )