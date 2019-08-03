# Travis CI telegram notifications

[![Build Status](https://travis-ci.org/vanyakosmos/travis-tg-notifier.svg?branch=master)](https://travis-ci.org/vanyakosmos/travis-tg-notifier)
[![Coverage](https://codecov.io/gh/vanyakosmos/travis-tg-notifier/branch/master/graph/badge.svg)](https://codecov.io/gh/vanyakosmos/travis-tg-notifier)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/vanyakosmos/travis-tg-notifier/tree/master)

## Usage

- go to [https://travis-tg.herokuapps.com](https://travis-tg.herokuapps.com)
- login via telegram
- use generated url as webhook in `.travis.yml`:

```
notifications:
  webhooks:
    - https://travis-tg.herokuapps.com/u/1234
```

- after each build you will receive notification from [@TravisCINotifierBot](https://t.me/TravisCINotifierBot).


## Usage 2

If you already know your telegram id (check it with [@JsonDumpBot](https://t.me/JsonDumpBot)) 
and you don't want to use auth then just append `/force` to the webhook.

You can also use this endpoint to post notifications into group chats (bot must be present in those groups).

```
notifications:
  webhooks:
    - https://travis-tg.herokuapps.com/u/TELEGRAM_ID/force
```

## Caveats

Similarly to problem with emails everyone who knows webhook url can use it in their builds. 
The good news is that "attackers" can't simulate travis-ci requests (ie use it out travis build scope) 
because webhook endpoint verifies signature from request against valid public key from travis-ci.
