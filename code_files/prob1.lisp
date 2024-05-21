; init memory
(alloc_num i 1000)
(alloc_num sum 0)

; def func
(def_func add_sum
    (set sum (+ (get_val sum) (get_val i)))
)

(while (get_val i) do
    (if (or
            (= (% (get_val i) 3) 0)
            (= (% (get_val i) 5) 0)
        ) then
        (add_sum @sum)
        else
    )
    (set i (- (get_val i) 1))
)

(output (get_val sum))
