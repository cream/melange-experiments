function Widget(name){

    this.name = name;

    this.callbacks = {};

    this.socket = new WebSocket('ws://127.0.0.1:8080');

    that = this; // TODO proper bind this
    this.socket.onopen = function(){
        var msg = {'type': 'init', 'name': that.name};
        this.send(JSON.stringify(msg));
    }

    this.socket.onmessage = function(e){

        var data = eval('(' + e.data + ')');
        if(data.type == 'init'){
            for(i=0; i < data.methods.length; i++){
                method = data.methods[i];
                that[method] = function(params, cb){
                    that.callRemote(method, params, cb);
                }
            }
        }
        else if(data.type == 'call'){
            alert(data.id);
            that.callbacks[data.id](data.data);
        }
    }

    this.callRemote = function(methodName, params, cb){
        var callback_id = '' + new Date().getTime();
        that.callbacks[callback_id] = cb;
        var msg = {'type': 'call', 'method': methodName, 'id': callback_id, 'args': params}
        that.socket.send(JSON.stringify(msg));
    }
}
