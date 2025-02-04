from operator import truediv
import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        # Iterate through all variables in the crossword:
        for variable in self.crossword.variables:
    # Check each word length in the crossword:
           for word_candidate in self.crossword.words:
        # Eliminate values inconsistent with the variable's unary constraints (word length):
                if len(word_candidate) != variable.length:
                   self.domains[variable].remove(word_candidate)

    def revise(self, x, y):
                    # Keep track of revised words for variable x
            revisions_x = []
            # Fetch overlaps for two arches
            overlap = self.crossword.overlaps[x, y]

            # If the variables do not overlap, no revision needed
            if overlap is None:
                return False

            # Iterate through word combinations in the domains of variable x
            for word_x in self.domains[x].copy():
                can_combine = False
                # Check each word in the domain of variable y
                for word_y in self.domains[y]:
                    # Check that the words overlap with the same letter
                    if word_x is not word_y and word_x[overlap[0]] is word_y[overlap[1]]:
                        can_combine = True
                        break
                # If cannot be combined, remove values from `self.domains[x]`
                # for which there is no possible corresponding value for `y` in `self.domains[y]`.
                if not can_combine:
                    revisions_x.append(word_x)
                    self.domains[x].remove(word_x)

            # Return True if a revision was made to the domain of `x`;
            # return False if no revision was made.
            if len(revisions_x) > 0:
                return True
            return False


        

    def ac3(self, arcs=None):      
        # If `arcs` is None, start with an initial list of all arcs in the problem.
        if arcs is None:
            arcs = []
            for var1 in self.crossword.variables:
                for var2 in self.crossword.neighbors(var1):
                    arcs.append((var1, var2))

        # Otherwise, use `arcs` as the initial list of arcs to make consistent.
        for arc_var1, arc_var2 in arcs:
            # Ensure that each variable is arc consistent by updating `self.domains`.
            if self.revise(arc_var1, arc_var2):
                for neighbor_var in self.crossword.neighbors(arc_var1):
                    arcs.append((arc_var1, neighbor_var))

        # Return True if arc consistency is enforced and no domains are empty;
        # return False if one or more domains end up empty.
        return len(self.domains[arc_var1]) > 0


    def assignment_complete(self, assignment):
        # For each variable, check if it is in keys or in words in crosswords
        for variable in self.crossword.variables:
            if variable not in assignment.keys() or assignment[variable] not in self.crossword.words:
                return False
        return True

    def consistent(self, assignment):
          # Check for consistency problems in the assignment
        for v1 in assignment:
            w1 = assignment[v1]

            # Ensure length matches
            if v1.length != len(w1):
                return False

            # Check combinations of two variables
            for v2 in assignment:
                w2 = assignment[v2]
                if v1 != v2:
                    # If two words are the same
                    if w1 is w2:
                        return False

                    overlap = self.crossword.overlaps[v1, v2]
                    if overlap is not None:
                        x, y = overlap
                        # If overlapping letters are wrong
                        if w1[x] != w2[y]:
                            return False

        # Return True if `assignment` is consistent (i.e., words fit in crossword
        # puzzle without conflicting characters)
        return True

    def order_domain_values(self, var, assignment):
        return self.domains[var]

    def select_unassigned_variable(self, assignment):
        for variable in self.crossword.variables:
            if variable not in assignment.keys():
                return variable
        return None

    def backtrack(self, assignment):
        # Check for completion to determine recursion termination
        if self.assignment_complete(assignment):
            return assignment

        # Iterate through unassigned variables
        current_variable = self.select_unassigned_variable(assignment)
        # Obtain values from the domain
        for possible_value in self.order_domain_values(current_variable, assignment):
            # Attempt to assign the value and check consistency
            assignment[current_variable] = possible_value
            if self.consistent(assignment):
                # Recursive call to find a solution; if the assignment makes a solution impossible, revert and continue
                result = self.backtrack(assignment)
                if result is None:
                    assignment[current_variable] = None
                else:
                    return result

        # If no assignment is possible, return None.
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
