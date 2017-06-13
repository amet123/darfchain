"""etherscan.io utilities."""

import time

from populus import Project

from ico.importexpand import expand_contract_imports


def _fill_in_textarea_value(browser, splinter_elem, value):
    """Do not do sendKeys() for large text.

    https://github.com/seleniumhq/selenium-google-code-issue-archive/issues/4469#issuecomment-192090165
    """
    elem = splinter_elem._element
    browser.driver.execute_script('''
        var elem = arguments[0];
        var value = arguments[1];
        elem.value = value;
    ''', elem, value)



def verify_contract(project: Project, chain_name: str, address: str, contract_name, contract_filename: str, constructor_args: str, libraries: dict, optimization=True, compiler: str="v0.4.8+commit.60cc1668", browser_driver="chrome") -> str:
    """Semi-automated contract verified on Etherscan.

    Uses a web browser + Selenium auto fill to verify contracts.

    See the page in action: https://etherscan.io/verifyContract?a=0xcd111aa492a9c77a367c36e6d6af8e6f212e0c8e

    :return: Contract expanded source code
    """

    try:
        from splinter import Browser
    except ImportError:
        raise RuntimeError("Splinter package must be installed for verification automation")

    src, imported_files = expand_contract_imports(project, contract_filename)

    if chain_name == "mainnet":
        url = "https://etherscan.io/verifyContract"
    elif chain_name == "ropsten":
        url = "https://ropsten.etherscan.io/verifyContract"
    elif chain_name == "kovan":
        url = "https://kovan.etherscan.io/verifyContract"
    else:
        raise RuntimeError("Unknown chain: ".format(chain_name))

    # Etherscan does not want 0x prefix
    if constructor_args.startswith("0x"):
        constructor_args = constructor_args[2:]

    with Browser(driver_name=browser_driver) as browser:
        browser.visit(url)

        browser.fill("ctl00$ContentPlaceHolder1$txtContractAddress", address)
        browser.fill("ctl00$ContentPlaceHolder1$txtContractName", contract_name)
        browser.select("ctl00$ContentPlaceHolder1$ddlCompilerVersions", compiler)
        browser.select("ctl00$ContentPlaceHolder1$ddlOptimization",  "1" if optimization else "0")
        #browser.fill("ctl00$ContentPlaceHolder1$txtSourceCode", src)
        #browser.find_by_name("ctl00$ContentPlaceHolder1$txtSourceCode").first.value = src
        _fill_in_textarea_value(browser, browser.find_by_name("ctl00$ContentPlaceHolder1$txtSourceCode"), src)
        _fill_in_textarea_value(browser, browser.find_by_name("ctl00$ContentPlaceHolder1$txtConstructorArguements"), constructor_args)
        #browser.fill("ctl00$ContentPlaceHolder1$txtConstructorArguements", constructor_args)

        idx = 1
        for library_name, library_address in libraries.items():
            browser.fill("ctl00$ContentPlaceHolder1$txtLibraryAddress{}".format(idx),library_address)
            browser.fill("ctl00$ContentPlaceHolder1$txtLibraryName{}".format(idx), library_name)
            idx += 1

        browser.find_by_name("ctl00$ContentPlaceHolder1$btnSubmit").click()

        deadline = time.time() + 60

        print("Waiting EtherScan to process the contract verification")
        while time.time() < deadline:
            if browser.is_text_present("Successfully generated ByteCode and ABI for Contract Address", wait_time=1):
                return src

            if browser.is_text_present("already been verified"):
                print("The contract has already been verified")
                return src

            time.sleep(1.0)

        print("Contract verification failed. Check the browser for details.")
        input("Press enter to continue")

    return src


def get_etherscan_link(network, address):
    """Construct etherscan link"""

    if network == "mainnet":
        return "https://etherscan.io/address/" + address
    elif network == "ropsten":
        return "https://ropsten.etherscan.io/address/" + address
    elif network == "kovan":
        return "https://kovan.etherscan.io/address/" + address
    else:
        raise RuntimeError("Unknown network: {}".format(network))
