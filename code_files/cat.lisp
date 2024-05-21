; init memory
(alloc_num val 0)

; transfer output to input
(input val)
(while (get_val val) do
    (output (get_val val))
    (input val)
)