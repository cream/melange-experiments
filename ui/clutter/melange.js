var DEBUG = false;

var _mootools_entered = new Array();

Element.Events.mouseenter = {
    base: "mouseover",
    condition: function(event){
        _mootools_entered.include(this);
        return true;
    }

};

var ConfigurationWrapper = new Class({
    Implements: Events,

    get: function(option) {
        return this._python_config[option];
    },

    set: function(option, value) {
        if(value === undefined) {
            /* Javascript allows this, but I don't want that. */
            throw new TypeError("`config.set` expects two arguments");
        }
        this._python_config[option] = value;
    },

    /*
     * Invoked on every gpyconf event.
     * Uses MooTools' Events for dispatching.
     */
    on_config_event: function() {
        /* `arguments` object to real `Array`: */
        var args = Array.prototype.slice.apply(arguments);
        /* First argument is the event name. */
        var event_name = args.shift();
        this.fireEvent(event_name, args);
    }
});

var Widget = new Class({
    init: function() {
    }
});

var widget = new Widget();

window.addEvent('domready', function() {
    if(window.main !== undefined) {
        widget.init();
        main();
    }
});
