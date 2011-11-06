import os
import sys
import math

from gi.repository import GtkClutter as gtkclutter
gtkclutter.init(sys.argv)

from gi.repository import Gtk as gtk, Cogl as cogl, Clutter as clutter, WebKit as webkit, JSCore as jscore, Gdk as gdk, GObject as gobject

BACKGROUND_IMAGE = 'Sommerspaziergang.jpg'

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

        for x in range(-width-4, width-4, 5):
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
    
        self.display = gdk.Display.get_default()
    
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

        settings = self.view.get_settings()
        settings.set_property('enable-plugins', False)
        self.view.set_settings(settings)

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.html')
        self.view.open('file://{0}'.format(path))

        self.widget = clutter.Group()
        self.widget.set_property('opacity', 255)
        self.stage.add_actor(self.widget)
        self.widget.show_all()
        
        self.widget.set_reactive(True)
        self.widget.connect('enter-event', self.widget_enter_event_cb)
        self.widget.connect('leave-event', self.widget_leave_event_cb)
        self.widget.connect('button-press-event', self.widget_button_press_event_cb)
        self.widget.connect('button-release-event', self.widget_button_release_event_cb)

        self.widget.set_position(200, 200)

        self.background = WidgetBackground(160, 160, 10)
        self.background.set_position(-5, -5)
        self.background.set_property('opacity', 0)
        self.widget.add_actor(self.background)
        self.background.show()

        self.wrapper = gtkclutter.Actor.new_with_contents(self.view)
        self.widget.add_actor(self.wrapper)
        self.wrapper.show_all()

        self.wrapper.connect('allocation-changed', lambda actor, box, flags: self.background.set_size(box.get_width() + 10, box.get_height() + 10))
        
        self.clone = clutter.Clone()
        self.clone.set_property('opacity', 0)
        self.clone.set_source(self.wrapper)
        self.widget.add_actor(self.clone)
        
        self.clone.set_reactive(True)
        self.clone.connect('button-release-event', self.widget_button_release_event_cb)

        self.window.show_all()
        self._moving = False
        
    
    def move(self, x=0, y=0):

        if self.moving:    
            new_x, new_y = self.display.get_pointer()[1:3]
            self.clone.set_position(new_x-x, new_y-y)

            gobject.timeout_add(20, self.move, x, y)
        return False


    @property
    def moving(self):
        return self._moving

    @moving.setter
    def moving(self, value):
        self._moving = value

    @moving.deleter
    def moving(self):
        del self._moving
        
      
    def widget_enter_event_cb(self, actor, event):
        self.background.animatev(clutter.AnimationMode.EASE_IN_QUAD, 100, ['opacity'], [80])
        
      
    def widget_leave_event_cb(self, actor, event):
        if not self.moving:
            self.background.animatev(clutter.AnimationMode.EASE_IN_QUAD, 300, ['opacity'], [0])
        
        
    def widget_button_press_event_cb(self, actor, event):

        if not self.moving:
            self.moving = True
            self.clone.animatev(clutter.AnimationMode.EASE_IN_QUAD, 50, ['opacity'], [100])
            gobject.timeout_add(20, self.move, self.display.get_pointer()[1], self.display.get_pointer()[2])
        
        
    def widget_button_release_event_cb(self, actor, event):

        if self.moving:
            self.moving = False
            self.clone.set_position(0, 0)
            self.clone.animatev(clutter.AnimationMode.EASE_IN_QUAD, 50, ['opacity'], [0])


Test()
gtk.main()
