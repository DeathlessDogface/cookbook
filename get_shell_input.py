from sys import argv

__all__ = ['get_shell_input', 'parse_type']


def get_shell_input():
    args = []
    kwargs = {}
    for i in argv:
        # parse map
        if "=" in i:
            k, v = i.split('=', 1)
            kwargs[k] = parse_type(v)
        # parse arr
        elif "," in i:
            args.append([parse_type(x) for x in i.split(',')])
        else:
            args.append(parse_type(i))
    return args, kwargs


def parse_type(input_str, boolean=True, lower=False, **kwargs):
    if input_str in kwargs:
        return kwargs[input_str]
    try:
        return int(input_str)
    except ValueError:
        pass
    try:
        return float(input_str)
    except ValueError:
        pass
    if input_str.lower() in ["none", "null", ""]:
        return None
    if input_str.lower() in ["yes", "ok", "true"] and boolean:
        return True
    if input_str.lower() in ["no", "false"] and boolean:
        return False
    if lower:
        return input_str.lower()
    return input_str


if __name__ == '__main__':
    args, kwargs = get_shell_input()
    print "args:", args
    print "kwargs:", kwargs
