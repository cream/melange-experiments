using Gtk;
using Clutter;
using GtkClutter;


const string BACKGROUND_IMAGE = "/home/kris/projects/cream/src/src/modules/melange-experiments/ui/clutter/Sommerspaziergang.jpg";


public class Test {

    public Gtk.Window window;
    public GtkClutter.Embed embed;
    public Clutter.Stage stage;
    public Clutter.Texture background;

    public Test() {

        this.window = new Gtk.Window();
        this.window.set_size_request(640, 480);

        this.window.destroy.connect( () => Gtk.main_quit());

        this.embed = new GtkClutter.Embed();
        this.window.add(this.embed);

        this.stage = (Clutter.Stage)this.embed.get_stage();

        this.background = new Clutter.Texture.from_file(BACKGROUND_IMAGE);
        this.stage.add_actor(this.background);


        this.window.show_all();
    }

    public static int main(string[] args) {

        var a = args;
        GtkClutter.init(ref a);

        var test = new Test();

        Gtk.main();

        return 0;
    }

}
