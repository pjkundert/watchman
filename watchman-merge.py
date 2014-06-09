#!/usr/bin/env python3

import csv

class rec:
    _fields			= [ "id", "last_name", "first_name", "age", "city", "prov", "country", "phone", "email", "unsubscribed", "invalid_email", "lists" ]

    def __init__( self, l ):
        for a,v in zip( self._fields, l ):
            if v == "NULL":
                v		= None
            setattr( self, a, v )
        # Names that are simply duplicates of email addresses (perhaps missing
        # extensions like '.com') are ignored.
        if self.first_name and self.email and '@' in self.first_name and self.first_name.lower() in self.email.lower():
            print("Rem: %s" % self.first_name)
            self.first_name	= ''
        if self.last_name and self.email and '@' in self.last_name and self.last_name.lower() in self.email.lower():
            print("Rem: %s" % self.last_name)
            self.last_name	= ''

    def __iter__( self ):
        """Produce the str representations of all fields"""
        for a in self._fields:
            v			= getattr( self, a )
            if v is None:
                yield "NULL"
            elif type( v ) is str:
                v.replace( '"', '\\"' )
                yield '"' + v + '"'
            else:
                yield str( v )

    def __str__( self ):
        return ','.join( self )

    def key( self ):
        """Usable as a dict key, two records with the same first/last name are identical (may differ on
        email address), but if no first/last name, then email is the key. """
        lname			= self.last_name
        fname			= self.first_name
        if lname or fname:
            return (lname or '', fname or '', '')
        return ('', '', self.email)

    def __eq__( self, other ):
        """Two elements with the same hash (first/last name and email) may NOT be equal!  This is how we
        determine differences; eg two Joe Blow <joe@blow.com> with different addresses).  Ignore 'id'"""
        if set( (self.email or '').split() ) != set( (other.email or '').split() ):
            return False
        return all( getattr( self, a ) == getattr( other, a )
                    for a in self._fields
                    if a not in ('id', 'email'))

    def __iadd__( self, other ):
        """Implements self += other: values from other override those in self.""" 
        if other.unsubscribed and not self.unsubscribed:
            self.unsubscribed	= 1
        if bool( other.invalid_email ) == bool( self.invalid_email ):
            # Both record's have identical email validity (good or bad).  Merge addresses.
            eu			= set( ( other.email or '').split() ) | set( ( self.email or '' ).split() )
            if eu:
                self.email	= ' '.join( eu )
        elif not other.invalid_email:
            # Our email is invalid, but the others is valid!  Use it
            self.invalid_email	= other.invalid_email
            self.email		= other.email

        for a in "age", "city", "prov", "country", "phone":
            if getattr( other, a ) and getattr( other, a ) != getattr( self, a ):
                setattr( self, a, getattr( other, a ))
        lu			= set( ( other.lists or '').split() ) | set( ( self.lists or '' ).split() )
        if lu:
            self.lists		= ' '.join( lu )
        return self

    # Make properties for any fields with special requirements

    # 
    # first_name
    # last_name
    #     Correct improper capitalization, replace O`...  with O'...
    def name_capitalize( self ):
        """Checks if the first and last names are non None or email addresses, then if "all lower" or "ALL
        UPPER"; if so, should capitalize."""
        if any( type( n ) is not str or '@' in n for n in (self._first_name, self._last_name)):
            return False
        if (   ( self._first_name.lower() == self._first_name and self._last_name.lower() == self._last_name )
            or ( self._first_name.upper() == self._first_name and self._last_name.upper() == self._last_name )):
            return True
        return False

    @property
    def last_name( self ):
        if self.name_capitalize():
            return self._last_name.capitalize()
        return self._last_name

    @last_name.setter
    def last_name( self, v ):
        self._last_name		= v if v is None else v.strip().replace( "`","'" )

    @property
    def first_name( self ):
        if self.name_capitalize():
            return self._first_name.capitalize()
        return self._first_name

    @first_name.setter
    def first_name( self, v ):
        self._first_name	= v if v is None else v.strip()

    # 
    # city
    #     Correct "city name" to "City Name", and remove trailing ", <prov>"
    @property
    def city( self ):
        if self._city is not None:
            city		= self._city
            if ',' in city:
                city 		= city.split( ',', 1 )[0]
            if city.lower() == city:
                return " ".join( n.capitalize() for n in city.split() )
            return city
        return self._city

    @city.setter
    def city( self, v ):
        self._city		= v

    # 
    # id
    # unsubscribed
    # invalid_email
    #     Numeric
    @property
    def id( self ):
        if self._id is not None:
            return int( self._id )
        return self._id

    @id.setter
    def id( self, v ):
        self._id	= v

    @property
    def unsubscribed( self ):
        if self._unsubscribed is not None:
            return int( self._unsubscribed )
        return self._unsubscribed

    @unsubscribed.setter
    def unsubscribed( self, v ):
        self._unsubscribed	= v

    @property
    def invalid_email( self ):
        if self._invalid_email is not None:
            return int( self._invalid_email )
        return self._invalid_email

    @invalid_email.setter
    def invalid_email( self, v ):
        self._invalid_email	= v

recsold				= {}
recsnew				= {}

for fn,dt,lbl in [('watchman-merge-old.csv', recsold, 'Old'),
                  ('watchman-merge-new.csv', recsnew, 'New')]:
    with open( fn, newline='', encoding='latin-1' ) as f:
        reader			= csv.reader( f, dialect="unix" )
        print( next( reader ))
        for l in reader:
            r			= rec( l )
            rk			= r.key()
            if rk in dt:
                # Dups with higher id's override earlier records.  Assume later records have higher ID
                print( "Dup: %s" % dt[rk] )
                print( "%s+ %s" % ( lbl, r ))
                dt[rk] 	       += r
                print( "   = %s" % dt[rk] )
            else:
                #print( "%s: %s" % ( lbl, r ))
                dt[rk]		= r


for rok,ro in recsold.items():
    if rok not in recsnew:
        #print( "Add: %s" % ro )
        recsnew[rok]		= ro
        continue
    rn				= recsnew[rok]
    if ro == rn:
        #print( "Equ: %s" % rn )
        continue

    # The old database's record differs.  We'll prefer the data from the old database.
    print( "Old: %s" % ro )
    print( " !=: %s" % rn )
    rn += ro
    print( " =>: %s" % rn )


# Output, re-numbering the records with id=1, but keeping them in existing id order.  Since we must
# output a bare "NULL" for None columns, we cannot use the csv writer, due to its limited handling
# of quoting.
with open( 'watchman-merge-fix.csv', 'w', newline='', encoding='latin-1' ) as f:
    #writer			= csv.writer( f, dialect="unix", quoting=csv.QUOTE_NONE, quotechar='\"', escapechar='\\' )
    #writer.writerow( rec._fields )
    i				= 1
    for r in sorted( recsnew.values(), key=lambda x: x.id ):
        r.id			= i; i += 1
        f.write( "%s\n" % r )
