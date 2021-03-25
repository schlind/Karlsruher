'''
    Delete all tweets that are older than a given age
'''
from datetime import datetime
from time import sleep

def delete_aged_tweets(karlsruher, max_age_days=7):
    '''

    :param karlsruher:
    :param max_age_days:
    '''

    karlsruher.logger.info('Deleting tweets older than %s days...', max_age_days)

    delete_count = 0
    oldest_id = None
    now = datetime.now()

    try:
        while True:

            tweets = karlsruher.api.user_timeline(count=200, max_id=oldest_id, trim_user=True)

            if not tweets:
                karlsruher.logger.info('No tweets to delete, cheers!')
                break

            for tweet in tweets:

                oldest_id = tweet.id

                ## baby maybe one day?
                #if tweet.favorite_count > 0:
                #    karlsruher.logger.info('Tweet is a favorite, now what?')
                #if tweet.retweet_count > 0:
                #    karlsruher.logger.info('Tweet is retweeted, now what?')

                tweet_age = now - tweet.created_at
                if tweet_age.days < max_age_days:
                    karlsruher.logger.info('Keeping tweet: %s' , tweet.id)
                    continue

                karlsruher.logger.info('Deleting tweet: %s',tweet.id)
                karlsruher.api.destroy_status(tweet.id)
                delete_count += 1

                sleep(0.25)

            karlsruher.logger.info('Number of tweets deleted: %s', delete_count)

            sleep(1)

    except KeyboardInterrupt:
        karlsruher.logger.info('Aborted! Number of tweets deleted: %s', delete_count)
