FILE_LIST = ./.installed_files.txt

.PHONY: pull clean dom install uninstall

default: | pull clean dom install

install:
	@ ./setup.py install --record $(FILE_LIST)

uninstall:
	@ while read FILE; do echo "Removing: $$FILE"; rm "$$FILE"; done < $(FILE_LIST)

clean:
	@ rm -Rf ./build

pull:
	@ git pull

dom:
	@ pyxbgen -u rentallib.xsd -m dom --module-prefix=rentallib
