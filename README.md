# p2p-tests
P2P Integration Tests, Development scripts etc

## Automated test process

By running python script from this directory and providing username and password for Bazaar you will initialize 
test procedure.

Before you begin make sure that your user have favorite peers in Subutai Bazaar and enough balance to use them.
It is required to have at least two peers. 

Script will create an environment from blueprint (defined in Subutai.json) and when environment become healthy
it will start local p2p client and establish a connection with the environment. 

Script will run several tests in background for 10 minutes in total and then shutdown evnironment and generate
test report.

## Running

Make sure you have python version 3 installed:

```
which python3
```
will output path to python binary: `/bin/python3`

Before you start you need to install PyYAML package:

```
pip install pyyaml
```

Configure application once by moving example configuration and changing its values:

```
mv config.yaml-example config.yaml
```

Now open this file and modify "email" and "password" values. Now you can run the script:

```
./auth.py
```

If you are getting Permission Denied error run the following command:

```
chmod +x ./auth.py
```

and then try again