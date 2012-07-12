from functools import partial
from chameleon import nodes, tal, i18n
from chameleon.astutil import Node
from chameleon.exc import ParseError, LanguageError
from chameleon.namespaces import XMLNS_NS, XML_NS, META_NS as META, I18N_NS as I18N, TAL_NS as TAL
from chameleon.utils import decode_htmlentities
from chameleon.zpt.program import MacroProgram, validate_attributes, skip, wrap


PRAMTAL = "http://www.microvac.co.id./namespaces/pramtal"

class BindChange(Node):
    """Element sequence."""

    _fields = "model_name", "bind_ons", "bind_attrs", "node", "start_tag"

class DefineModel(Node):
    """Element sequence."""

    _fields = "alias", "expression", "node"

class BindRepeat(Node):
    """Element sequence."""

    _fields = "alias", "expression", "node"

class Content(Node):
    """Element sequence."""

    _fields = "expression", "is_structure", "translate"

class BindingProgram(MacroProgram):
    DEFAULT_NAMESPACES = {
        'xmlns': XMLNS_NS,
        'xml': XML_NS,
        'tal': TAL,
        'i18n': I18N,
        'meta': META,
        'pramtal': PRAMTAL,
        }
    DROP_NS = TAL, I18N, META, PRAMTAL

    def __init__(self, *args, **kwargs):
        self.binds = kwargs.pop("binds", False)
        super(BindingProgram, self).__init__(*args, **kwargs)

    def visit_element(self, start, end, children):
        result = self.prev_visit_element(start, end, children)
        return result

    def prev_visit_element(self, start, end, children):
        ns = start['ns_attrs']

        for (prefix, attr), encoded in tuple(ns.items()):
            if prefix == TAL:
                ns[prefix, attr] = decode_htmlentities(encoded)

        # Validate namespace attributes
        validate_attributes(ns, TAL, tal.WHITELIST)
        validate_attributes(ns, I18N, i18n.WHITELIST)

        # Check attributes for language errors
        self._check_attributes(start['namespace'], ns)

        # Remember whitespace for item repetition
        if self._last is not None:
            self._whitespace = "\n" + " " * len(self._last.rsplit('\n', 1)[-1])

        # Set element-local whitespace
        whitespace = self._whitespace

        # Set up switch
        try:
            clause = ns[TAL, 'switch']
        except KeyError:
            switch = None
        else:
            switch = nodes.Value(clause)

        self._switches.append(switch)

        body = []

        content = nodes.Sequence(body)

        # tal:content
        try:
            clause = ns[TAL, 'content']
        except KeyError:
            pass
        else:
            key, value = tal.parse_substitution(clause)
            xlate = True if ns.get((I18N, 'translate')) == '' else False
            content = self._make_content_node(value, content, key, xlate)

            if end is None:
                # Make sure start-tag has opening suffix.
                start['suffix']  = ">"

                # Explicitly set end-tag.
                end = {
                    'prefix': '</',
                    'name': start['name'],
                    'space': '',
                    'suffix': '>'
                }

        # i18n:translate
        try:
            clause = ns[I18N, 'translate']
        except KeyError:
            pass
        else:
            dynamic = ns.get((TAL, 'content')) or ns.get((TAL, 'replace'))

            if not dynamic:
                content = nodes.Translate(clause, content)

        # tal:attributes
        try:
            clause = ns[TAL, 'attributes']
        except KeyError:
            TAL_ATTRIBUTES = {}
        else:
            TAL_ATTRIBUTES = tal.parse_attributes(clause)

        # i18n:attributes
        try:
            clause = ns[I18N, 'attributes']
        except KeyError:
            I18N_ATTRIBUTES = {}
        else:
            I18N_ATTRIBUTES = i18n.parse_attributes(clause)

        # Prepare attributes from TAL language
        prepared = tal.prepare_attributes(
            start['attrs'], TAL_ATTRIBUTES,
            I18N_ATTRIBUTES, ns, self.DROP_NS
        )

        # Create attribute nodes
        STATIC_ATTRIBUTES = self._create_static_attributes(prepared)
        ATTRIBUTES = self._create_attributes_nodes(
            prepared, I18N_ATTRIBUTES
        )

        # Start- and end nodes
        start_tag = nodes.Start(
            start['name'],
            self._maybe_trim(start['prefix']),
            self._maybe_trim(start['suffix']),
            ATTRIBUTES
        )
        stag = start_tag

        end_tag = nodes.End(
            end['name'],
            end['space'],
            self._maybe_trim(end['prefix']),
            self._maybe_trim(end['suffix']),
        ) if end is not None else None

        # tal:omit-tag
        try:
            clause = ns[TAL, 'omit-tag']
        except KeyError:
            omit = False
        else:
            clause = clause.strip()

            if clause == "":
                omit = True
            else:
                expression = nodes.Negate(nodes.Value(clause))
                omit = expression

                # Wrap start- and end-tags in condition
                start_tag = nodes.Condition(expression, start_tag)

                if end_tag is not None:
                    end_tag = nodes.Condition(expression, end_tag)

        if omit is True or start['namespace'] in self.DROP_NS:
            inner = content
        else:
            inner = nodes.Element(
                start_tag,
                end_tag,
                content,
            )

            # Assign static attributes dictionary to "attrs" value
            inner = nodes.Define(
                [nodes.Alias(["attrs"], STATIC_ATTRIBUTES)],
                inner,
            )

            if omit is not False:
                inner = nodes.Cache([omit], inner)

        # tal:replace
        try:
            clause = ns[TAL, 'replace']
        except KeyError:
            pass
        else:
            key, value = tal.parse_substitution(clause)
            xlate = True if ns.get((I18N, 'translate')) == '' else False
            inner = self._make_content_node(value, inner, key, xlate)

        # tal:define
        try:
            clause = ns[TAL, 'define']
        except KeyError:
            DEFINE = skip
        else:
            defines = tal.parse_defines(clause)
            if defines is None:
                raise ParseError("Invalid define syntax.", clause)

            DEFINE = partial(
                nodes.Define,
                [nodes.Assignment(
                    names, nodes.Value(expr), context == "local")
                 for (context, names, expr) in defines],
            )

        # tal:case
        try:
            clause = ns[TAL, 'case']
        except KeyError:
            CASE = skip
        else:
            value = nodes.Value(clause)
            for switch in reversed(self._switches):
                if switch is not None:
                    break
            else:
                raise LanguageError(
                    "Must define switch on a parent element.", clause
                )

            CASE = lambda node: nodes.Define(
                [nodes.Assignment(["default"], switch, True)],
                nodes.Condition(
                    nodes.Equality(switch, value),
                    node,
                )
            )

        # tal:repeat
        try:
            clause = ns[TAL, 'repeat']
        except KeyError:
            REPEAT = skip
        else:
            defines = tal.parse_defines(clause)
            assert len(defines) == 1
            context, names, expr = defines[0]

            expression = nodes.Value(expr)

            REPEAT = partial(
                nodes.Repeat,
                names,
                expression,
                context == "local",
                whitespace
            )

        # tal:condition
        try:
            clause = ns[TAL, 'condition']
        except KeyError:
            CONDITION = skip
        else:
            expression = nodes.Value(clause)
            CONDITION = partial(nodes.Condition, expression)

        # tal:switch
        if switch is None:
            SWITCH = skip
        else:
            SWITCH = partial(nodes.Cache, [switch])

        # i18n:domain
        try:
            clause = ns[I18N, 'domain']
        except KeyError:
            DOMAIN = skip
        else:
            DOMAIN = partial(nodes.Domain, clause)

        # i18n:name
        try:
            clause = ns[I18N, 'name']
        except KeyError:
            NAME = skip
        else:
            NAME = partial(nodes.Name, clause)

        # The "slot" node next is the first node level that can serve
        # as a macro slot
        slot = wrap(
            inner,
            DEFINE,
            CASE,
            CONDITION,
            REPEAT,
            SWITCH,
            DOMAIN,
        )

        slot = wrap(
            slot,
            NAME
        )

        # tal:on-error
        try:
            clause = ns[TAL, 'on-error']
        except KeyError:
            ON_ERROR = skip
        else:
            key, value = tal.parse_substitution(clause)
            translate = True if ns.get((I18N, 'translate')) == '' else False

            fallback = self._make_content_node(value, None, key, translate)

            if omit is False and start['namespace'] not in self.DROP_NS:
                fallback = nodes.Element(
                    start_tag,
                    end_tag,
                    fallback,
                )

            ON_ERROR = partial(nodes.OnError, fallback, 'error')

        clause = ns.get((META, 'interpolation'))
        if clause in ('false', 'off'):
            INTERPOLATION = False
        elif clause in ('true', 'on'):
            INTERPOLATION = True
        elif clause is None:
            INTERPOLATION = self._interpolation[-1]
        else:
            raise LanguageError("Bad interpolation setting.", clause)

        self._interpolation.append(INTERPOLATION)

        # Visit content body
        for child in children:
            body.append(self.visit(*child))

        self._switches.pop()
        self._interpolation.pop()

        slot = wrap(
            slot,
            ON_ERROR
        )
        try:
            define_model_clause = ns[(PRAMTAL, "define-model")]
        except KeyError:
            pass
        else:
            splits = define_model_clause.split(" ")
            if len(splits) != 2:
                raise LanguageError("Invalid define model.", define_model_clause)
            if not splits[0].startswith("#"):
                raise LanguageError("need # in alias.", define_model_clause)
            slot = DefineModel(splits[0][1:], splits[1], slot)

        stag.repeatable = False
        if self.binds:
            try:
                bind_repeat_clause = ns[(PRAMTAL, "bind-repeat")]
            except KeyError:
                pass
            else:
                splits = bind_repeat_clause.split(" ")
                if len(splits) != 2:
                    raise LanguageError("Invalid define model.", bind_repeat_clause)
                if not splits[0].startswith("#"):
                    raise LanguageError("need # in alias.", bind_repeat_clause)
                slot = BindRepeat(splits[0][1:], splits[1], slot)
                stag.repeatable = True


        stag.replayable = False
        if self.binds:
            try:
                bind_clause = ns[(PRAMTAL, "bind-change")]

                bind_splits = bind_clause.strip().split(" ")
                if  len(bind_splits) > 3:
                    raise LanguageError("Invalid bind syntax.", bind_clause)

                if not "#" in bind_splits[0]:
                    raise LanguageError("No bind model target specified.", bind_clause)
                first_split = bind_splits[0][1:]
                if "." in first_split:
                    bind_model,bind_ons = first_split.split(".", 1)
                    bind_ons = bind_ons.strip().split(".")
                else:
                    bind_model = ""
                    bind_ons = []

                bind_attrs = []
                if len(bind_splits) > 1:
                    bind_attrs = bind_splits[1].split(";")

                stag.replayable = True
                slot = BindChange(bind_model, bind_ons, bind_attrs, slot )
            except KeyError:
                pass


        return slot

    def _make_content_node(self, expression, default, key, translate):
        value = nodes.Value(expression)
        content = Content(value, key == "structure", translate)
        return content

