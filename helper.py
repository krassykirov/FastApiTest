from functools import wraps

def wrap(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        f = func.__name__
        write_log(f"function: {f} has been invoked")
        print('function_name:',f)
        return func(*args, **kwargs)
    return wrapper

def write_log(message=""):
    with open("log.txt", mode="a") as log_file:
        content = f"Log message: {message}"+ '\n'
        log_file.write(content)

# async def log(message: str, background_tasks: BackgroundTasks):
#     background_tasks.add_task(write_log, message="some notification")
#     return {"message": "Notification sent in the background"}