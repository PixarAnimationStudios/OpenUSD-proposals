# Motivation
Text can be used in a viewport editing environment in many different ways.  For instance, documentation publishing, user interface elements, markup and comments, etc.  When using USD and Hydra for rendering in a design app it is important that the USD and Hydra framework supports text elements.

NOTE: in this design, the text primitive should be within a plane, or in general it is a 2D text. Deformable 3D text is not included in this design.

# The features of text
The text could be single-line single-style text, or multiple-line multiple-style text.

NOTE: Single-line single-style text is not a multiple-line multiple-style text whose line count and style count is 1. Because the implementation of single-line single-style text can be more optimized. 

### Single line single style text properties
The text properties are commonly called text style.
<details>
<summary>Common text styles</summary>

| property name |   example   |  comment  |
|:--------:|:---------:|:-----------|
|  typeface  |![](typeface.jpg)| The name string of the font |
|  Bold  |![](bold.jpg)| Bold is the property of a font. |
|  Italic  |![](italic.jpg)| Italic is the property of a font. |
|  Weight  |![](weight.jpg)| For some font library such as GDI, you can define the weight of the stroke. But Freetype doesn't have this feature. |
|  Height  |![](Size.jpg)| For some font, the appearance of a character may change when height of the character changes. |
|  Width factor  |![](width.jpg)| The factor will be multiplied to the width of each character, including the white space. |
|  Oblique  |![](oblique.jpg)| Oblique is a transform of the text mesh. It is different from italic, which is not a transform, but a property of font. |
|  Character spacing  |![](characterSpace.jpg)| Character spacing is the space between characters. |
|  Underline  |![](undelrine.jpg)| Underline is used for emphasis, comment or error mark. Underline could have line style. |
|  Overline  |![](overline.jpg)| Overline is not commonly used. |
|  Strikethrough  |![](strikethrough.jpg)| Strikethrough is used when you delete some text and want to keep the history at the same time. Sometimes we use two lines for strikethrough. |
|  Color  |![](color.jpg)|  |
|  Background color  |![](bgcolor.jpg)|  |

</details>

Single line single style text can have special layout.
<details>
<summary>Common text layout</summary>

| property name |   example   |  comment  |
|:--------:|:---------:|:-----------|
|  Direction  |![](direction.jpg)| Some languages are written from left to right, while others are written right to left, such as Arabic. The Chinese characters can be written from left to right, from right to left and from top to bottom. |

</details>

### Multiline multi-style text properties
<details>
<summary>Common multiline text layout</summary>

| property name |   property value  |  example   |  comment  |
|:--------:|:---------:|:---------:|:-----------|
|  Markup language  |  |![](MTEXT.jpg)| The markups will define the style of the subsequent string. |
|  Line space  |  |![](linespace.jpg)| The space between two lines in the same paragraph. |
|  Lines flow direction  | Right to left |![](RTL.jpg)| For some special language such as the Traditional Chinese script, while the baseline of the text goes from top to bottom, the flow direction of the lines can be from right to left (by default), or from left to right.  |
|  Lines flow direction  | Left to right |![](LTR.jpg)|  |
|  Paragraph space  |  |![](ParagraphSpace.png)| The space after the paragraph and before the next paragraph. |
|  Paragraph indents  | First-line indent |![](FirstLineIndent.jpg)| The space before the first character of the first line in the paragraph. |
|  Paragraph indents  | Left indent |![](leftindent.png)|  |
|  Paragraph indents  | Right indent |![](rightindent.png)|  |
|  Tab stops  |  |![](tabstops.png)| By default, the tabs all have the same pre-defined length. But you can also specify tab-stop position in the paragraph. The text after a tab will be just positioned at the tab stop. There are four tab-stop types: left, right, center and decimal. |
|  Paragraph alignment  | Left align |![](LeftAlign.jpg)| How the words or characters are distributed in a line in the paragraph. |
|  Paragraph alignment  | Center align |![](CenterAlign.jpg)|  |
|  Paragraph alignment  | Right align |![](RightAlign.jpg)|  |
|  Paragraph alignment  | Justify align |![](Justify.jpg)|  |
|  Paragraph alignment  | Distributed align |![](distribute.jpg)|  |
|  Column  |  |![](Column.jpg)| Column is the rectangle blocks that the multiline text will be put in. It is common in the layout of a web page, that when the width of the page is too wide, we will split the page into several blocks so that the width of one block will not be so wide.  |
|  Column alignment |  |![](columnAlignment.png)| How the text content in the column is aligned in the vertical direction. |
|  Column margin |  | ![](margins.png) | Column margins are the borders in the four directions. |

This is a picture which illustrates what are the column margins and paragraph indents in an office word page.
![](marginsAndIndents.png)

</details>

The work proposed here aims to tackle all of these properties. Those not listed can be considered in future works.

### Rendering technique
There are already many different techniques which can display the text on screen. One commonly used technique is MSDF, that generate the multi-channel signed distance field for each character, and use it to reconstruct the shape of the glyph. Another technique is to get the control points of the curves which form the outline of the characters, and then render the curves on the screen. Different techniques may have different quality and performance. 

# The single line single style text schema
A new primitive SimpleText is added, which inherits from Gprim. It inherits properties from Gprim. The primitive is for a single line single style text. "Single line" means that the baseline of the characters is straight and there is no line break. "Single style" means the appearance style for the characters are assumed to be the same. Here, we use "assume" because the user would like that the style is the same, but in the implementation, a part of the characters may not be supported so it may use an alternate style to display the characters. That is, although in schema level we use one text style for the SimpleText, on the screen some characters may still be rendered with a different style.

A typed schema TextStyle will represent the appearance style of the text string. An API schema TextStyleAPI is provided to bind the TextStyle to a SimpleText primitive. One TextStyle can be bound to several different SimpleText primitives. One SimpleText must bind one and at most one TextStyle.

There is another API schema TextLayoutAPI which is used to set the direction of the SimpleText.

### Properties inherited from Gprim
- doublesided
- extent
- orientation
- purpose
- visibility
- xformOpOrder
- primvars:displaycolor
- primvars:displayopacity

The primvars:displaycolor and the primvars:displayopacity will be the color and opacity of the SimpleText.

### Properties specialized for SimpleText
- textData. The text data is a UTF-8 string. This property must be specified for SimpleText.
  - The textData string is the default string for all languages. You can use a language tag to specify an alternate textData for a specified language. For example, using "textData:fr" to add an alternate text string for French. In that case, if the user would like to display the French string, they could use the alternate string. For more detail about the multiple language support, please read [this proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/language). (Currently the language tag is not supported in our implementation. Will be implemented in the future.)
- primvars:backgroundColor. The color of the background. By default there is no background color. (Currently this not supported in our implementation. Will be implemented in the future.)
- primvars:backgroundOpacity. The opacity of the background. By default there is no background opacity. (Currently this not supported in our implementation. Will be implemented in the future.)
- textMetricsUnit. The unit for text metrics, such as text height. It is a string token, which could be "pixel", "publishingPoint" or "worldUnit". By default it is "worldUnit". If textMetricsUnit is "pixel", the unit of text metrics will be the same as a pixel in the framebuffer. If textMetricsUnit is "publishingPoint", the unit will be the same as desktop publishing point, or 1/72 of an inch on a screen's physical display. If textMetricsUnit is "worldUnit", the unit will be the same as the unit of the world space. If the text primitive has billboard, the textMetricsUnit can only be "pixel" or "publishingPoint". Otherwise, the textMetricsUnit can only be "worldUnit".

### Properties of TextStyle and TextStyleAPI
The TextStyle class includes the following properties:

- font:typeface. The string for the font name. This property must be specified for TextStyle. There is no default value.
- font:format. This is a string token, which could be "ttf/otf", "fon", "pcf", "shx" and any other font types. Because most of the font library has the similar handling for ttf font and otf font, we use "ttf/otf" for both ttf font and otf font. By default the fontType is "ttf/otf".
- font:altTypeface. The string for an alternate font name. Sometimes not all characters can be displayed with the typeface above. We will try to display the missing characters with this alternate typeface. If it is still missing, it is up to the implementation to handle the missing characters. By default this string is empty. (Currently this not supported in our implementation. Will be implemented in the future.)
- font:altFormat. This is a string token which works like the font:format, but it is the format for font:altTypeface. If font:altTypeface is not set, this property will be ignored. By default it is "ttf/otf". (Currently this not supported in our implementation. Will be implemented in the future.)
- font:weight. An int value for font weight. By default, it is 0, which means the weight value is ignored. In that case, the value of font:bold will be valid. We use the definition of weight in CSS. (Currently this not supported in our implementation. Will be implemented in the future.)
  - Here is a table how the weight is mapped to a font style in CSS.
  
  | weight value |   font style  |
  |:--------:|:---------:|
  | 100 | Thin |
  | 200 | Extra Light |
  | 300 | Light |
  | 400 | Normal(Regular) |
  | 500 | Medium |
  | 600 | Semi Bold |
  | 700 | Bold |
  | 800 | Extra Bold |
  | 900 | Ultra Bold |
- font:bold. A boolean value. It will specify if the font style is bold. It is valid only when font:weight is zero. Or else, we will ignore this value. By default it is false. 
- font:italic. A boolean value. It will specify if the font style is italic. By default it is false.
- charHeight. An int value represents the height of the text. This property must be specified for TextStyle. There is no default value. The unit is textMetricsUnit. If you want to get a float text height, you need to use a scale matrix.
- obliqueAngle. A float value for the skew angle between the character's left line and the vertical axis. The unit is degree. By default it is zero.
- charWidthFactor. A float value for the scale factor of the character width. By default it is 1.0.
- charSpacingFactor. A float value. This is defined as the scale factor of the character width plus the character space. By default it is 1.0.
- underlineType. This is a string token, which could be "none" or "normal". "none" means there is no underline. "normal" means the underline is a normal line. You can define other type of underline. By default it is "none".
- overlineType. This is a string token, which could be "none" or "normal". "none" means there is no overline. "normal" means the overline is a normal line. You can define other type of overline. By default it is "none".
- strikethroughType. This is a string token, which could be "none", "normal" or "doubleLines". "none" means there is no strikethrough. "normal" means the strikethrough is a normal line. "doubleLines" means the strikethrough is double lines. You can define other type of strikethrough. By default it is "none".

The TextStyleAPI class doesn't have extra properties.

### Properties of TextLayoutAPI
Currently, the layout of a text primitive includes the direction of the baseline of a text line, and the direction how the text lines are stacked. By default, we don't give a preset for the direction. It is decided by the implementation. For example, most implementation will arrange the Latin characters from left to right, and Arabic characters from right to left. And the text lines are stacked from top to bottom.

You can still explicitly set the direction using the TextLayoutAPI.

Currently the TextLayoutAPI class includes the following properties:

- layout:baselineDirection. This is a string token reprensents the direction of the baseline of a text line. The value could be "upToImpl", "leftToRight", "rightToLeft", "topToBottom" or "bottomToTop". By default it is "upToImpl", which means the direction is decided by the implementation. "leftToRight" means the text is written from left to right. "rightToLeft" means the text is written from right to left. "topToBottom" means the text is written from top to bottom. "bottomToTop" means the text is written from bottom to top. (Currently in our implementation the direction will always be "upToImpl". The other settings will not take effect, but will be implemented in the future.)
- layout:linesStackDirection. This is a string token reprensents the direction how the text lines are stacked. The value could be "upToImpl", "leftToRight", "rightToLeft", "topToBottom" or "bottomToTop". By default it is "upToImpl", which means the direction is decided by the implementation. "leftToRight" means the text lines are stacked from left to right. "rightToLeft" means the text lines are stacked from right to left. "topToBottom" means the text lines are stacked from top to bottom. "bottomToTop" means the text lines are stacked from bottom to top. (Currently in our implementation the flow direction will always be "upToImpl". The other settings will not take effect, but will be implemented in the future.)

The baselineDirection and linesStackDirection must be perpendicular. For example, if the baselineDirection  is "leftToRight" or "rightToLeft", the linesStackDirection can only be either "topToBottom" or "bottomToTop". Or else, the implementation will be confused. And if the baselineDirection  is "topToBottom" or "bottomToTop", the linesStackDirection must be either "leftToRight" or "rightToLeft".

By applying the TextLayoutAPI, you can set the direction. For SimpleText, as there is only one line, only the layout:baselineDirection will take effect. The layout:linesStackDirection will be ignored.

### Extents of SimpleText
SimpleText is not point based, so we need to calculate the extents. This calculation requires that we generate the layout of the SimpleText. In the implementation, we need to add the utility functions to generate the layout for SimpleText in UsdText domain. As the calculation of extents is complex, we need to save the layout in UsdTextSimpleText, so that we can reuse it.

# The multi-line multi-style text schema
A new primitive MarkupText is added, which inherits from Gprim. It inherits properties from Gprim. This primitive represents a text object which can have one line or multiple lines, and it can have varied styles. This requires a way to represent the layout of the text data, and the style of each character. The MarkupText uses the markup language to represent the layout and the style. For the layout, the markups could define the place where a line break is added, where a new paragraph starts, and the style of a paragraph. For the style, the markups could define the text style for a part of the string.

The TextStyle schema are used to represent the default text style for the primitive. You can use TextStyleAPI schema to bind a TextStyle to a MarkupText primitive. It is not required that MarkupText must bind a TextStyle. And one MarkupText can bind at most one TextStyle. The style defined by the markup will override the default text style.

A MarkupText primitive can have no paragraph. And it can have one or multiple paragraphs. The count of paragraphs is defined by the markups. We add a schema ParagraphStyle which is used to represent the paragraph style. You can use ParagraphStyleAPI schema to bind a ParagraphStyle to a MarkupText primitive. The style defined by the markup will override the current paragraph style.

One MarkupText is not required to bind a ParagraphStyle. And one MarkupText can bind one or more ParagraphStyles. If the MarkupText bind more than one ParagraphStyle, the ParagraphStyles will be applied to the paragraphs defined in the string in order. If the markup string contains more paragraphs than the count of ParagraphStyles, the last ParagraphStyle will be applied to the last several paragraphs that don't have the corresponding ParagraphStyle.

For example, if an MarkupText binds two ParagraphStyles with the name "P1" and "P2". 
- If the string is a plain string "This is a plain string" with no markup, there will be no paragraphs, and the two paragraph styles will not take effect.
- If the string is an MText string "\PThere is one paragraph", there will be one paragraph, and the paragraph style will be "P1". The "P2" style will not take effect. 
- If the string is an MText string "\PThis is the first paragraph.\PThis is the second paragraph.", there will be two paragraphs, and the first paragraph has the style "P1" while the second 
one has the style "P2". 
- If the string is an MText string "\PThis is the first paragraph.\PThis is the second paragraph.\PThis is the third paragraph.", there will be three paragraphs, and the first paragraph has the style "P1" while the second and the third one have the style "P2". 

People are used to define a constraint for a text object, so that line break will be automatically added at the border. For MarkupText, we define a column as the constraint. And the ColumnStyle will be used to describe the column. You can use ColumnStyleAPI schema to bind a ColumnStyle to a MarkupText primitive. The column style defined by the markup will override the current column style. 

A MarkupText will have at least one column, and it can have more than one column. The count of columns is defined by how many ColumnStyles are bound to the MarkupText primitive. The column breaks defined in the markup string will move the following text into the next column. 

One MarkupText must bind at least one ColumnStyle. If the text string is too long, that the height of the lines overflow the height of the column, the behaviour is up to the implementation. The implementation can choose that the characters can run out of the column, or it can also choose to truncate the string. If the markup string contains more column breaks than the count of ColumnStyles, it will meet with column breaks in the last Column. In that case, the behaviour is up to the implementation. It can choose to ignore the column break, or truncate the following string.

Like the TextStyle, one ColumnStyle or ParagraphStyle can be bound to multiple different MarkupText primitives.

You can also apply a TextLayoutAPI to the MarkupText primitive, to set the baseline direction and the stack direction of the lines. The ColumnStyle may also be applied with a TextLayoutAPI, and in that case, the layout of the Column will override the layout of the whole MarkupText.

### Properties inherited from Gprim
- doublesided
- extent
- orientation
- purpose
- visibility
- xformOpOrder
- primvars:displaycolor
- primvars:displayopacity

The primvars:displaycolor and the primvars:displayopacity will be the default color and opacity of the MarkupText. They can be override by the color and opacity value in the markup string.

### Properties specialized for MarkupText
- markup. The text data could be interpreted as a markup string. There is no default value. This must be specified for MarkupText.
  - The markup string is the default string for all languages. You can use a language tag to specify an alternate string for a specified language. For example, using "markup:fr" to add an alternate text string for French. In that case, if the user would like to display the French string, they could use the alternate string. For more detail about the multiple language support, please read [this proposal](https://github.com/PixarAnimationStudios/OpenUSD-proposals/tree/main/proposals/language).
  - You can also use "markup:plain" to add an alternate string when the markup language is not supported by the implementation. This alternate string must have no markup. It will be used if the implementation can not resolve the markups in the default string.
- markupLanguage. It is a string token tells how the markup tags are interpreted. Currently we support "plain" which is for plain text string, and "mtext" which is for MTEXT markups. By default it is "plain".
- primvars:backgroundColor. The color of the background. By default there is no background color. It can be overridden by the specified background color in the markup. (Currently this not supported in our implementation. Will be implemented in the future.)
- primvars:backgroundOpacity. The opacity of the background. By default there is no background opacity. The background is completely transparent. It can be overridden by the specified background color in the markup. (Currently this not supported in our implementation. Will be implemented in the future.)
- textMetricsUnit. The unit for text metrics, such as text height. It is a string token, which could be "pixel", "publishingPoint" or "worldUnit". By default it is "worldUnit". If textMetricsUnit is "pixel", the unit of text metrics will be the same as a pixel in the framebuffer. If textMetricsUnit is "publishingPoint", the unit will be the same as desktop publishing point, or 1/72 of an inch on a screen's physical display. If textMetricsUnit is "worldUnit", the unit will be the same as the unit of the world space. If the text primitive has billboard, the textMetricsUnit can only be "pixel" or "publishingPoint". Otherwise, the textMetricsUnit can only be "worldUnit".

### Properties of ColumnStyle and ColumnStyleAPI
Currently the ColumnStyle class includes the following properties:

- columnWidth. A float value for width. Zero means that the column doesn't have constraint in width. By default it is zero. The unit is textMetricsUnit.
- columnHeight. A float value for height. Zero means that the column doesn't have constraint in height. By default it is zero. The unit is textMetricsUnit.
- columnOffset. Two float values for the offset from the origin of the MarkupText to the origin of this column. By default the two floats are zero. The unit is textMetricsUnit.
- margins. Four float values for the margins of the column, the order is left margin, right margin, top margin and bottom margin. By default all the margins are zero. The unit is textMetricsUnit.
- columnAlignment. The columnAlignment is the vertical alignment of the text. It is a string token, which could be "top", "center" and "bottom". By default it is "top".

The ColumnStyleAPI class doesn't have extra properties.

The ColumnStyle can be applied with a TextLayoutAPI, to set the baseline direction and the stack direction of the lines in the Column.

### Properties of ParagraphStyle and ParagraphStyleAPI
Currently the ParagraphStyle class includes the following properties:

- firstLineIndent. It is an float value for the indent in the first line. By default it is zero. The unit is textMetricsUnit.
- leftIndent. It is an float value for the indent on the left of the paragraph. By default it is zero. The unit is textMetricsUnit.
- rightIndent. It is an float value for the indent on the right of the paragraph. By default it is zero. The unit is textMetricsUnit.
- paragraphAlignment. A string token which could be "left", "center", "right", "justify", and "distributed". By default it is "left".
- paragraphSpace. A float value for the space after the paragraph and before the next paragraph. By default it is zero. The unit is textMetricsUnit.
- tabstops. A paragraph could have several tabstops. Each tabstop has the below properties:
  - tabstopType. It is a string token which could be "leftTab", "rightTab", "centerTab", or "decimalTab". By default it is "leftTab".
  - position. It is an float value for the position of the tabstop. This must be specified for a tabstop. The unit is textMetricsUnit.
- lineSpace. A float value for the line space in this paragraph. By default it is zero. The unit is textMetricsUnit.
- lineSpaceType. This is a string token, which could be "exactly", "atLeast" or "multiple". By default it is "exactly", which means the lineSpace value is exactly the space between lines.

The ParagraphStyleAPI class doesn't have extra properties.

### Extents of MarkupText
MarkupText is not point based, so we need to calculate the extents. This calculation requires that we generate the layout of the MarkupText. In the implementation, we need to add the utility functions to generate the layout for MarkupText in UsdText domain. As the calculation of extents is complex, we need to save the layout in UsdTextMarkupText, so that we can reuse it.

# Some implementation details
### Text with extrusion
Some users would like to have the 2D text with extrusion. Extrusion is a common transform that can convert a planar object into a 3D object. It can not only applied on text, but also on many planar shape such as a pie or a square. The user can extend our SimpleText or MarkupText schema by adding an extrudeDepth primvar, or applying an extrude API schema. To implement a text with extrusion, the implementation need to generate a detailed 2D mesh for a 2D text, and add the side faces to form the extrusion.

### Handle missing characters
It is common that the font in the TextStyle can not support all the characters in the text string. In that case, we say the characters are missing. If the TextStyle has the font:altTypeface property, the implementation should try to use the alternate font to display the characters. If it is still missing, one common solution is to use a default character of the font for the missing characters. Or the implementation can still try to find another font which can support the characters.

### Generate layout for complex script
By default, it is up to the implementation to generate the layout. For complex script such as Arabic, Hebrew and Dedevanagari, it is best that the implemetation could identify the script and knows how to generate the ligatures and handle the contextual shaping. If the implementation can not handle the features of complex script, we suggest that it could just arrange the glyphs from left to right in order.

### Billboard
Billboarding is a way of adding special transformations to a geometry - anchoring to the screen, scaling to the screen instead of the world, etc. When there is extension to enable billboarding for Gprims, as SimpleText and MarkupText are type of Gprims, billboarding will be automatically enabled for them.

# Example
### A SimpleText with a TextStyle
This is a SimpleText primitive. The text string is "The clever brown fox", no matter what language the user wants. The textMetricsUnit is world unit (default value). The direction is up to the implementation (default value). The primitive binds a TextStyle. The font is "Times New Roman Bold"(timesbd.ttf), and the height of the characters are 100 world unit. There will be one overline on the text string.
```
def SimpleText "TextA" (
    prepend apiSchemas = ["TextStyleAPI"]
){
    uniform string textData = "The clever brown fox"
    rel textStyle:binding = </StyleA>
}

def TextStyle "StyleA" {
    uniform string font:typeface = "Times New Roman"
    uniform bool font:bold = 1
    uniform int charHeight = 100
    uniform token overlineType = "normal"
}
```
### A SimpleText with a TextStyle and applied with a TextLayoutAPI
This is a SimpleText primitive. The text string is "The clever brown fox" if the language required is not Arabic. For Arabic language, we will use the alternate string "الثعلب البني الذكي". The textMetricsUnit is world unit (default value). The direction is right to left, which means no matter the required language is English or Arabic, the characters should be arranged from right to left. The primitive binds a TextStyle. The font weight is 600, which will convert to SemiBold style. Because both Consolas and Courier New typeface doesn't have SemiBold style, we will use the bold style instead. So the font will be "Consolas bold italic"(consolaz.ttf). But if the language is Arabic, because Consolas doesn't support the language, we will use the alternate font "Courier New bold italic"(courbi.ttf). The height of the characters are 100 world unit. The characters' width will be widen by 20 percent, and the character space will be widen by 10 percent. And there will be double lines strikethrough on the text string.
```
def SimpleText "TextA" (
    prepend apiSchemas = ["TextStyleAPI"]
    prepend apiSchemas = ["TextLayoutAPI"]
){
    uniform string textData = "The clever brown fox"
    uniform string textData:Ar = "الثعلب البني الذكي"
    rel textStyle:binding = </StyleA>
    uniform token layout:baselineDirection = "rightToLeft"
}

def TextStyle "StyleA" {
    uniform string font:typeface = "Consolas"
    uniform string font:altTypeface = "Courier New"
    uniform int font:weight = 600
    uniform bool font:italic = 1
    uniform int charHeight = 100
    uniform float charWidthFactor = 1.2
    uniform float charSpacingFactor = 1.1
    uniform token strikethroughType = "doubleLines"
}
```
### A MarkupText with a TextStyle and a ColumnStyle
This is a MarkupText primitive. The text string is a plain string that has no markup. The textMetricsUnit is world unit (default value). The primitive binds a TextStyle, which will be the default style for the primitive. The font is "Times New Roman Bold"(timesbd.ttf), and the height of the characters are 40 world unit. The primitive also binds a ColumnStyle. The column width is 500, so line break will be inserted when the text line layout goes out of the right border of the column. The four column margins are all zero (by default). And the alignment is top (default value).
```
def MarkupText "TextA" (
    prepend apiSchemas = ["TextStyleAPI"]
    prepend apiSchemas = ["ColumnStyleAPI"]
)
{
    uniform string markup = "If you format a document with columns (as in some newsletter layouts), the text will automatically flow from one column to the other. You can insert your own column breaks for more control over the document format."
    rel textStyle:binding = </StyleA>
    rel columnStyle:binding = </ColumnA>
}

def TextStyle "StyleA" {
    uniform string font:typeface = "Times New Roman"
    uniform bool font:bold = 1
    uniform int charHeight = 40
}

def ColumnStyle "ColumnA" {
    uniform float columnWidth = 500
    uniform float columnHeight = 300
    uniform float2 columnOffset = (0.0, 0.0)
}
```
### A MarkupText with a TextStyle, a ColumnStyle and two ParagraphStyles
This is a MarkupText primitive. The text string contains "mtext" markup. The primitive binds a TextStyle which will works as the default text style. So by default, the font is "Arial Regular" (arial.ttf), and the height is 40. But the markup defines that the font of a part of the text has bold style, so a part of the text will use the font "Arial Bold" (arialb.ttf). The markup also defines a part of the text has underline. And the markup adds two paragraph breaks to the string, so the whole string will be divided into 3 paragraphs.

The primitive provides an alternate string for French language. The string doesn't contain markup so it will use the default text style. The primitive also provides an alternate string if the markup can not be parsed by the implementation. The string will also use the default text style.

The textMetricsUnit is pixel. The primitive may be put in a screen space billboard.

The primitive binds a ColumnStyle. The column width is 500, so line break will be inserted when the text line layout goes out of the right border of the column. The column also defines the four margins, and the alignment is center. The ColumnStyle is applied with TextLayoutAPI. The baselineDirection will be from right to left for this column, and the lines are stacked from top to bottom.

The primitive binds to two ParagraphStyles, each has a different style. Because the text string is divided into 3 paragraphs by the markups, the first ParagraphStyle will be applied to the first paragraph, and the second ParagraphStyle will be applied to the second and third paragraph. If the implementation uses the string for French language or string without markup, there will be no paragraph, so the ParagraphStyles will be ignored.
```
def MarkupText "TextA" (
    prepend apiSchemas = ["TextStyleAPI"]    
    prepend apiSchemas = ["ParagraphStyleAPI"]
    prepend apiSchemas = ["ColumnStyleAPI"]
)
{
    uniform string markup = "If you format a document with \\fArial|b1;columns\\fArial|b0; (as in some newsletter layouts), \\Pthe text will automatically flow from one column to the other. \\PYou can insert your own \Lcolumn breaks\\l for more control over the document format."
    uniform string markup:fr = "Colonne et saut de colonne"
    uniform string markup:plain = "If you format a document with columns (as in some newsletter layouts), the text will automatically flow from one column to the other. You can insert your own column breaks for more control over the document format."
    uniform token markupLanguage = "mtext"
    uniform token textMetricsUnit = "pixel"
    rel textStyle:binding = </StyleA>
    rel columnStyle:binding = </ColumnA>
    rel paragraphStyle:binding = [
                </ParagraphA>,
                </ParagraphB>,
            ]
}

def TextStyle "StyleA" {
    uniform string font:typeface = "Arial"
    uniform int charHeight = 40
}

def ColumnStyle "ColumnA" (
    prepend apiSchemas = ["TextLayoutAPI"]
)
{
    uniform float columnWidth = 500
    uniform float columnHeight = 400
    uniform float2 columnOffset = (0.0, 0.0)
    uniform float4 margins = (10.0, 10.0, 20.0, 20.0)
    uniform token columnAlignment = "center"
    uniform token layout:baselineDirection = "rightToLeft"
    uniform token layout:linesStackDirection = "topToBottom"
}

def ParagraphStyle "paragraphA" {
    uniform float leftIndent = 0.0
    uniform float rightIndent = 0.0
    uniform float firstLineIndent = 20.0
    uniform float paragraphSpace = 0.0
    uniform token lineSpaceType = "exactly"
    uniform float lineSpace = 30.0
}

def ParagraphStyle "paragraphB" {
    uniform float leftIndent = 0.0
    uniform float rightIndent = 0.0
    uniform float firstLineIndent = 20.0
    uniform float paragraphSpace = 0.0
    uniform token paragraphAlignment = "right"
}
```