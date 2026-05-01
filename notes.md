04/28/26 12:18 AM - 1:08 AM
Currently I am only able to take in 1 streamer at a time --> Trying to take in up to 10
I am thinking about splitting the data by key, where the key is the target_channel.
    This would also require more consumer groups?
    Probably more partinions too (too keep up with the raised load)
Problem --> Twitch EventSub API only allows 3 connections per account
    Could create more accounts, but this would not be user friendly in a production app
    We subscribe to all channels using one login token.
Problem --> How to load in multiple variables from an env variable.
    comma seperate the variable in the env file
        load the variable in with .split by comma
Problem --> consumer is only consuming from the last element in the TARGET_CHANNEL env variable   
    Problem --> Maybe the consummer is only subscribing to the first channel it takes in?
        Maybe Producer is having the same problem, because we are sending all on the same topic anyways, so the consumer should data from all channels in right?
    I was right it is only consuming from the last element in the target channel env. 

04/28/26 6:03 PM - 7:44 PM
    Had to use an aync generator, but still not working. 
    Tried wrapping the listen_channel_chat_message chall in a for loop looping around targets (maybe we were landing on the last target and sticking with that?)
        CORRECT!!
Problem --> injestion is slow (only 1 message per batch)
    reduce batch size to 1 kb 
    change linger.ms to 2000ms
        throughput dsrastically increased
    Also changed to higher message streamers to increase (msg/s)

TODO: implement the final backend which writes to PosgreSQL DB and frontend
    Subproblems:
    Create SQL schema
        make db local to user computer
    Connect SQL db to user
    Create React Frontend
    Connect Backend to Frontend
    Connect Backend to DB

    Dockerize everything into one container
        Including Kafka
        Database
        Backend and frontend


        Find a way to increase partitions
            find a way to increase consumers
                in-turn increasing throughput
    
04/29/26 12:25 PM - 4:40 PM
Trying to make code more modular
    thinking about splitting into 2 folders
        consumer, injestion + producer, and main on the outside
        
Added 8 partionions to docker-compose to increase throughput
Tested using Docker Lag the lag in increasing over 10 seconds (6954 --> 7151) so the ML model is slowing us down
    Changed to use Apple GPU via pytorch mps, now there is no lag (Optimized hardware)
    Sentiment is calculated on a buffer calssifying them in one forward pass. Bounded by draining 32 messages at a time from Kafka or a 500ms flush so the latency stays real time.

05/01/26 3:44 PM - 

Initilized Django API and DB
Created DB Models
    Need to work more on making the DB models more relational and easier to work together

