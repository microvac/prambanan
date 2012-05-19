import colander
import translationstring

Anu = colander.Range

range = colander.Range(min=12, max =20)
i = Anu()
a = translationstring.TranslationStringFactory("a")
