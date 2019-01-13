#!/usr/bin/awk -f
$2 == "1" && $4 ~ /^[^\.]+\.[^\.]+$/ {
    dom = $4;
    split(dom,a,".");
    name = a[1];
    top = a[2];
    ltop = length(top)
    lname = length(name)

    if (lname>7) next;
    if (name ~ /-/) next;

    gtop = top ~ /^(com|net|org|wtf|es|tv|pi|me|my|si|one|pro|pub|xyz|info|mobi|tk|ninja)$/;

    if (ltop>2 && !gtop) next;

    if (lname<4) {
        print dom;
        next;
    }
    if (lname==4 && name ~ /^[0-9]$/) {
        print dom;
        next;
    }
    if (name ~ /[0-9]/ || name !~ /[aeiou]/) {
        next;
    }

    print dom;
}
