import tldextract, sys, uuid, json, os, importlib

BROWSER_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append( BROWSER_PATH );

class ProjectHelper():
    def __init__(self):
        self.lista = None;
        pass;
    def list(self):
        if self.lista == None:
            self.lista = [];
            lista = os.listdir(os.path.join(os.environ["BROWSER_PATH"], "projects"));
            self.lista = [];
            for item in lista:
                if not os.path.exists(os.path.join(os.environ["BROWSER_PATH"], "projects", item, "config.json")):
                    continue;
                js = json.loads( open(os.path.join(os.environ["BROWSER_PATH"], "projects", item, "config.json"), "r").read() );
                if js["active"]:
                    module_spec = importlib.util.spec_from_file_location( js["module"], os.path.join(os.environ["BROWSER_PATH"], "projects", item, js["path"])  ) ;
                    module = importlib.util.module_from_spec(module_spec);
                    module_spec.loader.exec_module(module);
                    class_obj = getattr(module, js["name"]);
                    object_dynamic = class_obj();
                    self.lista.append( object_dynamic );
        return self.lista;