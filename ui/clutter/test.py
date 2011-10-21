import os
import sys
import math
from gi.repository import Gtk as gtk, Cogl as cogl, Clutter as clutter, GtkClutter as gtkclutter, WebKit as webkit, JSCore as jscore, Gdk as gdk, GObject as gobject

gtkclutter.init(sys.argv)

BACKGROUND_IMAGE = '/home/stein/Bilder/Hintergrundbilder/cream.png'

FRAMERATE = 30.0

CURVE_LINEAR = lambda x: x
CURVE_SINE = lambda x: math.sin(math.pi / 2 * x)

def rounded_rectangle(cr, x, y, w, h, r=20):
    # This is just one of the samples from
    # http://www.cairographics.org/cookbook/roundedrectangles/
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #   F****E

    cr.move_to(x+r,y)                      # Move to A
    cr.line_to(x+w-r,y)                    # Straight line to B
    cr.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
    cr.line_to(x+w,y+h-r)                  # Move to D
    cr.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
    cr.line_to(x+r,y+h)                    # Line to F
    cr.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
    cr.line_to(x,y+r)                      # Line to H
    cr.curve_to(x,y,x,y,x+r,y)             # Curve to A


class WidgetBackground(clutter.CairoTexture):
    """Base actor for a rounded retangle."""

    def __init__(self, width, height, arc):

        clutter.CairoTexture.__init__(self)
        self.set_surface_size(width, height)
        self.connect('draw', self.draw_cb)
        self.create()

        self.invalidate()


    def draw_cb(self, texture, ctx):

        width, height = self.get_surface_size()

        ctx.set_source_rgba(255, 255, 255, .5)
        rounded_rectangle(ctx, 2, 2, width - 4, height - 4, 10)
        ctx.stroke()

        rounded_rectangle(ctx, 3, 3, width - 6, height - 6, 10)
        ctx.clip()

        ctx.set_source_rgba(255, 255, 255, .3)
        ctx.set_line_width(1)

        for x in xrange(-width-4, width-4, 5):
            ctx.move_to(x, height - 2)
            ctx.line_to(x+width-4, 2)
        ctx.stroke()


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

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.html')
        self.view.open('file://{0}'.format(path))

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

        rect = WidgetBackground(170, 170, 10)
        rect.set_position(203, 222)
        self.stage.add_actor(rect)
        rect.show()

        self.window.show_all()


Test()
gtk.main()
