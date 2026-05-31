(define (problem bw-3-blocks)
  (:domain blocksworld)
  (:objects a b c - block)
  (:init
    (ontable a) (clear a)
    (ontable b) (clear b)
    (ontable c) (clear c)
    (handempty)
  )
  (:goal
    (and (on a b) (on b c) (ontable c))
  )
)
