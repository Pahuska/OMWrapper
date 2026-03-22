import inspect

def test(*args, machin=None, **kwargs):
    print(args)
    print(machin)
    print(kwargs)

# def test(a, b, c, machin=None, **kwargs):
#     print(a, b, c)
#     print(machin)
#     print(kwargs)

sig = inspect.signature(test)
bound_args = sig.bind(1,2,3, machin='ABC', truc=True, bidule=None)
bound_args.apply_defaults()
arguments = bound_args.arguments

do_args = []
do_kwargs = {}
for param in sig.parameters.values():
    name = param.name
    value = arguments[name]
    if param.kind == param.POSITIONAL_ONLY:
        do_args.append(value)
    elif param.kind == param.VAR_POSITIONAL:
        do_args.extend(value)
    elif param.kind == param.VAR_KEYWORD:
        do_kwargs.update(value)
    else:
        do_kwargs[name] = value

print(do_args, do_kwargs)
test(*do_args, **do_kwargs)