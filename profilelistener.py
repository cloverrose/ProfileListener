# -*- coding:utf-8 -*-
""" Tweepy's StreamListener to get User object """
import json
from tweepy.streaming import StreamListener
from tweepy.models import Status, User
from tweepy.utils import parse_datetime


class ProfileListener(StreamListener):
    def __init__(self, api):
        super(ProfileListener, self).__init__(api)
        self.friends = []
        self.my_id = self.api.verify_credentials().id
        # print 'my_id: {0}'.format(self.my_id)

    def on_status(self, user, created_at):
        return

    def on_follow(self, user, created_at):
        return

    def on_unfollow(self, user, created_at):
        return

    def on_friends(self, friends):
        return

    def parse_status_event(self, data):
        """
        if status contains user-object then return parsed user-object,
        else return False.

        ** NOTE **
        this method treats tweet and RT,
        but other data also contains '"in_reply_to_status_id":', e.g. fav.
        """
        if '"in_reply_to_status_id":' not in data:
            return False
        jobj = json.loads(data)
        if 'user' not in jobj or 'created_at' not in jobj:
            return False
        user = User.parse(self.api, jobj['user'])
        if user.id != self.my_id and user.id not in self.friends:
            return False
        created_at = parse_datetime(jobj['created_at'])
        return dict(user=user, created_at=created_at)

    def parse_follow_unfollow_event(self, data):
        """
        if data is follow or unfollow event-object then return parsed event-object,
        else return False.
        """
        if '"event":"follow"' not in data and '"event":"unfollow"' not in data:
            return False
        jobj = json.loads(data)
        if 'event' not in jobj or 'created_at' not in jobj or 'target' not in jobj:
            return False
        event_name = jobj['event']
        if event_name != 'follow' and event_name != 'unfollow':
            return False
        target = User.parse(self.api, jobj['target'])
        if event_name == 'follow' and target.id == self.my_id:  # User is followed
            return False
        created_at = parse_datetime(jobj['created_at'])
        return dict(event_name=event_name, created_at=created_at, target=target)

    def parse_friends_event(self, data):
        """
        if data is friends event-object then return parsed event-object,
        else return False.
        """
        if not data.startswith('{"friends":['):
            return False
        jobj = json.loads(data)
        if 'friends' not in jobj:
            return False
        return jobj['friends']

    def on_data(self, data):
        status = self.parse_status_event(data)
        if status is not False:
            user = status['user']
            created_at = status['created_at']
            # print 'status    {0} {1}({2})'.format(created_at, user.name, user.screen_name)
            if self.on_status(user, created_at) is False:
                return False
            return

        event = self.parse_follow_unfollow_event(data)
        if event is not False:
            user = event['target']
            created_at = event['created_at']
            if event['event_name'] == 'follow':
                # print 'follow    {0} {1}({2})'.format(created_at, user.name, user.screen_name)
                self.friends.append(user.id)
                if self.on_follow(user, created_at) is False:
                    return False
                return
            else:
                # print 'unfollow  {0} {1}({2})'.format(created_at, user.name, user.screen_name)
                self.friends.remove(user.id)
                if self.on_unfollow(user, created_at) is False:
                    return False
                return

        friends = self.parse_friends_event(data)
        if friends is not False:
            self.friends = friends
            # print 'friends: {0}'.format(self.friends)
            if self.on_friends(friends) is False:
                return False
            return


if __name__ == '__main__':
    import tweepy
    from tweepy.streaming import Stream
    from tweepy.auth import OAuthHandler

    consumer_key = 'XXXXXXXXXXXXXXXXXXXXXX'
    consumer_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    access_key = 'xxxxxxx-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
    access_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth_handler=auth)
    stream = Stream(auth, ProfileListener(api), secure=True)
    stream.userstream()
