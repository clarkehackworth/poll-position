poll-position
=============

Poll Position can be used to stuff some online polls with fake results

Online polls sometimes limit voting based on IP address.  This script retrieves lists of free proxy servers with which it votes through.  
Multiple free proxy lists are retrieved from specific internet sites.  The script will cycle through each proxy list and is configurable to sequentially or randomly choose a proxy from the list.

The script also so contains some cheating detection subversion mechanisms:

1. configurable randomization of time between successfull votes (looks more like human voting)

2. only votes when you are not winning by a configurable amount.  This means you don't get to far ahead in the poll that it looks like you are cheating.  
