(define (problem BLOCKS-4-0)
(:domain BLOCKS)
(:objects B A C - block)
(:init (CLEAR C) (CLEAR A) (CLEAR B) (ONTABLE C) (ONTABLE A)
 (ONTABLE B) (HANDEMPTY))
(:goal (AND (ON C B) (ON B A)))
)
