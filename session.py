
jump_to_bottom = False

def cast_bool(current, new):
    new = new.lower()
    if new == "false":
        return False
    if new == "true":
        return True
    return current

def match_and_assign(lval, rval):
    global jump_to_bottom

    if lval == "jump_to_bottom":
        jump_to_bottom = cast_bool(jump_to_bottom, rval)
            


def parse_session(session_str):
    for statement in session_str.split(";"):
        statement = statement.split("=")

        if len(statement) != 2:
            continue

        lval = statement[0].strip()
        rval = statement[1].strip()

        match_and_assign(lval, rval)


def to_string():
    session = ""
    session +="jump_to_bottom="+str(jump_to_bottom)
    return session
