(define (problem BLOCKS-6-1)
(:domain BLOCKS)
(:objects A B C D - block)
(:INIT (CLEAR C) (ONTABLE A) (CLEAR B) (ONTABLE D) (ON B D) (ON C A) (HANDEMPTY))
(:goal (AND (ON A C) (ON C D) (ON D B)))
)
