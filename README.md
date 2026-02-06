# Larry_engine
A super basic game engine for 2d development, includes sprite editor, custom language and script editor and save/load system.

SYNTAX:
Variables:
  -assigning values/creating: decree <var> = <val> (can be string or integer or float)
  - assigning user input to a variable: decree <var> = ask "<prompt>"
  - assigning random numbers to a variable: decree <var> = random between <min> and <max>
Mathematical operations:
  -note only one operation can be performed per line, and either two variables, two numbers or a variable and a number can be used
  -addition: decree sum = <val 1> plus <val 2>
  -subtraction: decree diff = <val 1> - <val 2>
  -multiplication: decree prod = <val 1> times <val 2>
  -division: decree quot = <val 1> divide <val 2>
Output:
  -the declare command is used to print output to the consol
  -print a string: declare "<string>"
  -print the value of a variable: declare <var>
  -concatenation: declare "<string>" + <var>
Control Flow:
  -conditions are: is greater than, is less than, is equal to, is not equal to
  -if statement: if <condition>
                    ...
                 elif <condition>
                    ...
                 else
                    ...
                 end if
  -while loop: while <condition>
                        ...
                      end loop
  -for loop: for every <item> in <list> OR for every <var> in <min num> to <max num>
                  ...
              end loop

Lists:
  -note lists do not yet support variables as items
  -creating: decree <list> = [<item 1>, <item 2>]
  -accessing: decree <item> = <list> at <index>
  -modifying: decree <list> at <index> = <item>
  -length: decree <var> = <list> length
Window and sprite management:
  -open window: open window x <val> y <val>
  -change background colour: background <colour>
  -stretch sprite to fill backgtound: fill background <sprite name>
  -tile a sprite to fill background: tile background <sprite name>
  -spawn a sprite: spawn <sprite name> x <x pos> y <y pos>
  -change sprite x and y: change <sprite name> <axis> by <val>
  -check for collisions: if is colliding <sprite 1> <sprite 2> (note if collisions are enabled in the sprite editor for two sprites, the will automattically collide / not pass through each other)
  -resize a sprite: resize <sprite> <amount>%
  -get sprite x or y: decree <var> = get <sprite> <axis>
  -check for keypresses: if key pressed <key> (note supports only letter keys so far)
