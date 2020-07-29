# Travis CI telegram notifications

[![Build Status](https://travis-ci.org/vanyakosmos/travis-tg-notifier.svg?branch=master)](https://travis-ci.org/vanyakosmos/travis-tg-notifier)
[![Coverage](https://codecov.io/gh/vanyakosmos/travis-tg-notifier/branch/master/graph/badge.svg)](https://codecov.io/gh/vanyakosmos/travis-tg-notifier)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/vanyakosmos/travis-tg-notifier/tree/master)

## Usage

- go to [https://travis-tg.herokuapp.com](https://travis-tg.herokuapp.com)
- login via telegram
- use generated url as webhook in `.travis.yml`:

```
notifications:
  webhooks:
    - https://travis-tg.herokuapp.com/u/CHAT_ID
```

- after each build you will receive notification from [@TravisCINotifierBot](https://t.me/TravisCINotifierBot).


## Usage without telegram authentication or in group chats

- initiate dialog with [@TravisCINotifierBot](https://t.me/TravisCINotifierBot) or add it to the chat.
- type `/webhook` to receive webhook url for current chat
- copy-n-paste webhook url into `.travis.yml`

```
notifications:
  webhooks:
    - https://travis-tg.herokuapp.com/u/CHAT_ID
```
