import sys
import math
from gi.repository import Gtk as gtk, Clutter as clutter, GtkClutter as gtkclutter, WebKit as webkit, JSCore as jscore, Gdk as gdk, GObject as gobject

gtkclutter.init(sys.argv)

BACKGROUND_IMAGE = '/home/stein/Bilder/Hintergrundbilder/cream.png'

FRAMERATE = 30.0

CURVE_LINEAR = lambda x: x
CURVE_SINE = lambda x: math.sin(math.pi / 2 * x)

class Timeline(gobject.GObject):

    __gtype_name__ = 'Timeline'
    __gsignals__ = {
        'update': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_FLOAT,)),
        'completed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ())
        }

    def __init__(self, duration, curve):

        gobject.GObject.__init__(self)

        self.duration = duration
        self.curve = curve

        self._states = []
        self._stopped = False


    def run(self):

        n_frames = (self.duration / 1000.0) * FRAMERATE

        while len(self._states) <= n_frames:
            self._states.append(self.curve(len(self._states) * (1.0 / n_frames)))
        self._states.reverse()

        gobject.timeout_add(int(self.duration / n_frames), self.update)


    def stop(self):
        self._stopped = True


    def update(self):
        
        if self._stopped:
            self.emit('completed')
            return False

        self.emit('update', self._states.pop())
        if len(self._states) == 0:
            self.emit('completed')
            return False
        return True


class Test(object):

    def __init__(self):
    
        self.window = gtk.Window()
        #self.window.set_type_hint(gdk.WindowTypeHint.DESKTOP)
        #self.window.set_size_request(1440, 900)
        self.window.set_size_request(640, 480)
        
        self.window.connect('destroy', lambda *args: gtk.main_quit())

        self.embed = gtkclutter.Embed()
        self.window.add(self.embed)

        self.stage = self.embed.get_stage()

        self.background = clutter.Texture()
        self.background.set_from_file(BACKGROUND_IMAGE)
        self.stage.add_actor(self.background)

        self.view = webkit.WebView()
        self.view.set_transparent(True)
        self.view.open('file:///home/stein/Labs/Experiments/melange-clutter/test.html')

        self.widget = gtkclutter.Actor.new_with_contents(self.view)
        
        def show():
            self.stage.add_actor(self.widget)
            self.widget.set_position(200, 200)
            self.widget.set_property('opacity', 0)
            self.widget.show_all()
            
            self.widget.set_property('scale-gravity', clutter.Gravity.CENTER)
            
            def update_cb(t, s):
                self.widget.set_property('opacity', min(255, int(round(255*s))))
                #self.widget.set_property('scale-x', s)
                #self.widget.set_property('scale-y', s)

            timeline = Timeline(200, CURVE_SINE)
            timeline.connect('update', update_cb)
            
            timeline.run()
            
            """
            animation.set_key(self.widget, "scale-x", clutter.AnimationMode.EASE_OUT_BACK, 0.0, 0.0)
            animation.set_key(self.widget, "scale-x", clutter.AnimationMode.EASE_OUT_BACK, 1.0, 1.0)

            animation.set_key(self.widget, "scale-y", clutter.AnimationMode.EASE_OUT_BACK, 0.0, 0.0)
            animation.set_key(self.widget, "scale-y", clutter.AnimationMode.EASE_OUT_BACK, 1.0, 1.0)

            animation.start()
            """

            return False
            
        gobject.timeout_add(1000, show)

        self.view.connect('status-bar-text-changed', self.call_cb)

        self.window.show_all()
        

    def call_cb(self, view, text):
    
        if text == 'hermes-call':
            hermes = self.view.get_dom_document().get_element_by_id('hermes')
            print gobject.signal_list_names(hermes)
            print "JS-PY:", hermes.get_inner_html()
            
            self.view.execute_script('py_to_js("BLUBB");')
            

Test()
gtk.main()
