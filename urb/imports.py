import glob
import os                       # os.path getmtime, join

from twisted.internet.task import LoopingCall

from urb.util import dlog, dtrace


def _get_module(module_path):
    return __import__(module_path, globals(), locals(), ['*'])

def _get_attr(full_attr_name):
    """Retrieve a module attribute from a full-dotted package name."""
                
    # Parse out the path, module, and function
    last_dot = full_attr_name.rfind(u".")
    attr_name = full_attr_name[last_dot + 1:]
    module_path = full_attr_name[:last_dot]
                                    
    module_obj = _get_module(module_path)
    attr_obj = getattr(module_obj, attr_name)

    # Return a reference to the function itself,
    # not the results of the function.
    return attr_obj, module_obj
                                                        
def _get_func(full_func_name):
    func_obj, module_obj = _get_attr(full_func_name)
    assert callable(func_obj), "%s is not callable." % full_func_name
    return func_obj, module_obj

def _get_class(full_class_name, parent_class=None):
    """
    Load a module and retrieve a class (NOT an instance).
    If the parentClass is supplied, className must be of parentClass
    or a subclass of parentClass (or None is returned).
    """
    class_obj, module_obj = _get_func(full_class_name)
    # Assert that the class is a subclass of parentClass.
    if parent_class is not None:
        if not issubclass(class_obj, parent_class):
            raise TypeError(u"%s is not a subclass of %s" %
                            (full_class_name, parent_class))
    # Return a reference to the class itself, not an instantiated object.
    return class_obj, module_obj

_loaded_module_objects = {} 

def _get_mtime(abspath):
    if abspath.endswith('pyc'):
        abspath = abspath[:-1]
    return os.path.getmtime(abspath)
    
def _check_module_change(submodule):
    modtup = _loaded_module_objects[submodule]
    oldtime = modtup[1]
    curtime = _get_mtime(modtup[0].__file__)
    if curtime > oldtime:
        dlog("The %s module has changed, refreshing..." % submodule)
        refresh(submodule)
        
def _check_for_changes():
    for submodule, modtup in _loaded_module_objects.iteritems():
        _check_module_change(submodule)
        
if __debug__:
    LoopingCall(_check_for_changes).start(0.5)
        
def refresh( submodule ):
    if submodule in _loaded_module_objects:
        module, mtime = _loaded_module_objects[submodule]
        dlog("Attempting reload '%s'..." % submodule)
        try:
            module = reload(module)
        except Exception, e:
            dtrace("There was an error reloading %s :" % module.__file__)
            return False
        finally:
            dlog("Successfully refreshed %s." % submodule)
            _loaded_module_objects[submodule] = (module, _get_mtime(module.__file__))
            return True
    else:
        return False

def load_all(modulename):
    submodules = get_all(modulename)
    dynamics = {}
    for sub in submodules:
        dynamics[sub] = get(modulename, sub)
    return dynamics

def get_all( modulename ):
    module = _get_module('urb.%s' % modulename)
    module_list = []
    if module:
        path = module.__file__
        path = path[:path.rfind("/")]
        for infile in glob.glob(os.path.join(path, '*.py')):
            name = infile[infile.rfind("/") + 1:]
            if not name == '__init__.py':
                submodule = name[:-3]
                module_list.append(submodule)
        return module_list            

def get( module, submodule ):
    if submodule in _loaded_module_objects:
            return _loaded_module_objects[ submodule ][0].exported_class
    full_path = '.'.join( ['urb', module, submodule, 'exported_class'] )
    try:
        cls, mod = _get_class(full_path)
        dlog("Dynamically loaded %s from %s" % (cls, mod.__file__))
        _loaded_module_objects[ submodule ] = mod, _get_mtime(mod.__file__)
        return cls
    except Exception, e:
        dtrace("Exception dynamically importing %s.%s" % (module, submodule))
        return None
