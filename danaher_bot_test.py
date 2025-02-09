
import praw

reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent=os.environ.get("REDDIT_USER_AGENT")
)

# Check read access: fetch the top 5 posts from a subreddit
for submission in reddit.subreddit("bjj").hot(limit=10):
    print(submission.title)


