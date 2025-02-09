.gitignore

import praw

reddit = praw.Reddit(
    client_id="71rkosnFXt2NZBvyOz9N7A",
    client_secret="4E2h1YhnGLcoYobQlMY6gtmJcQ4qKg",
    user_agent="trends_danaher_bot/0.1 by Classic_Visual4481"
)

# Check read access: fetch the top 5 posts from a subreddit
for submission in reddit.subreddit("bjj").hot(limit=10):
    print(submission.title)


