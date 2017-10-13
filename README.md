## dnChatNetwork

Our project consists of multi-clients and multi servers connecting with each other in acyclcic topology as well in cyclic. It still has a few bugs. The recent addition we did was displaying the clients that were already connected when a new user connected with a server. We handled the deletetion of users from the lists that disconnects from the server. And handled the acknowledgements while broadcasting as well as sending to specific user.

### Functionality

The dnChatNetwork can send broadcast messages to all the clients connected in a server. Not only a single server but also in a network of servers the implementation works fine. We can send a message to a specific user too. We handle the client or server leaving or arriving in the network and successfully notifying all.

We are also handling a few conditions other than this that are quite useful if implemented on a bigger scale like checking for a malformed message, checking for duplicate clients etc.
