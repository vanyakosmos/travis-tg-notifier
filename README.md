# Travis CI telegram notifications

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

## Caveats

Similarly to problem with emails everyone who knows webhook url can use it in their builds. 
But "attackers" can't simulate travis-ci requests because webhook endpoint verifies signature 
from request against valid public key from travis-ci.
