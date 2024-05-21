; init memory
(alloc_str hello "Hello, ")
(alloc_buf name 30)
(alloc_num addr 0)
(alloc_num len 0)
(alloc_num val 0)

; def func print
(def_func print
    (set addr $1)
    (set len (get_by_addr addr))
    (while (get_val len) do
        (set len (- (get_val len) 1))
        (set addr (+ (get_val addr) 1))
        (output (get_by_addr addr))
    )
)

; read name
(set len 0)
(set addr name)
(input val)
(while (get_val val) do
    (set addr (+ (get_val addr) 1))
    (set len (+ (get_val len) 1))
    (set (get_val addr) (get_val val))
    (input val)
)
(set name (get_val len))

; print "Hello, "
(print @hello)

; print name
(print @name)
